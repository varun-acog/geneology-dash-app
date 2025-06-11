import duckdb
import polars as pl

DATABASE_URL = r"data/lineage.db"

engine = duckdb.connect(DATABASE_URL, read_only=True)

__all__ = ["get_lineage", "get_item_codes", "get_product_codes"]

def get_product_codes() -> list[dict]:
    """
    Fetch distinct Product Codes from ItemMaster table.
    Returns a list of dictionaries with 'label' and 'value' for dropdown options.
    """
    query = """
    SELECT DISTINCT ProductCode
    FROM ItemMaster
    WHERE ProductCode IS NOT NULL
    ORDER BY ProductCode
    """
    result = engine.execute(query).pl()
    
    # Convert to list of dictionaries for Dash dropdown
    product_codes = [
        {"label": code, "value": code}
        for code in result["ProductCode"].to_list()
    ]
    
    return product_codes

def get_item_codes(search_value) -> list[dict]:
    pr_in = engine.execute("""select types.ITEMCODE as "ItemCode", im.Category, im.ProductCode, im.Description, im.UnitOpName, im.tag
                    FROM 
                    vw_ListOfTypes types
                    LEFT JOIN ItemMaster im ON im.ItemCode = split_part(types.ITEMCODE, '-', 1)
                    where types.ITEMCODE IS NOT NULL
                    AND types.ITEMCODE ilike '%{}%'
                   """.format(search_value)).pl()
    
    result_list = (
        pr_in.with_columns([
            pl.struct([
                pl.when(pl.col("ProductCode").is_not_null())
                .then(pl.col("ProductCode") + " - " + pl.col("ItemCode"))
                .otherwise(pl.col("ItemCode"))
                .alias("label"),
                pl.col("ItemCode").alias("value")
            ]).alias("item_dict")
        ])
        .select("item_dict").to_series().to_list()
    )
    
    return result_list

def get_lineage(
    startNodes,
    endNodes=None,
    outputtype="polars",
    GenOrTrc="all",
    level=-99,
    outputcols="default",
    product_code=None
):
    """
    Function to get the results of the query in the specified format, with optional Product Code filter.
    :param startNodes: List of Item codes, Lot Numbers, Parent Lot or Supplier Lot Numbers to trace.
    :param endNodes: List of Item codes, Lot Numbers, Parent Lot to target.
    :param outputtype: The output type, either 'polars' or 'duckdb'.
    :param GenOrTrc: 'gen', 'trc', or 'all' to specify genealogy, traceability, or both.
    :param level: Maximum recursion level for the query.
    :param outputcols: Columns to include in the output.
    :param product_code: Optional Product Code to filter results.
    :return: The result of the query in the specified format.
    """
    if level == -99:
        qrylevel = 99
    elif level is None:
        qrylevel = 99
    else:
        qrylevel = level

    func_Source(startNodes, GenOrTrc, qrylevel)  # refresh trace temp tables

    if endNodes is not None:
        func_Target(endNodes)  # refresh target temp tables
        strwheretrc = " where EXISTS (select 1 from tmp_tracetarget WHERE lot_number = product_lot)"
        strwheregen = " where EXISTS (select 1 from tmp_tracetarget WHERE lot_number = ingredient_lot)"
    else:
        strwheretrc = " where 1=1"
        strwheregen = " where 1=1"

    # Execute Gen or Trc or Both queries
    qrystrGen, qrystrTrc = "", ""

    if GenOrTrc == "trc" or GenOrTrc == "all":
        qrystrTrc = f"""
        select 'Trc'as type, 
        root_itemcode as root_itemcode,
        root_parentlot as root_parentlot,
        root_lot as root_lot,
        root_supplierlot as root_supplierlot,
        level,
        product_itemcode as product_itemcode,
        product_lot as product_lot,
        product_pln as product_parentlot,
        CASE WHEN level = 1 THEN root_itemcode ELSE ingredient_itemcode END as ingredient_itemcode,
        CASE WHEN level = 1 THEN root_lot ELSE ingredient_lot END as ingredient_lot,
        CASE WHEN level = 1 THEN root_supplierlot ELSE ingredient_supplierlot END as ingredient_supplierlot,
        CASE WHEN level = 1 THEN root_parentlot ELSE ingredient_pln END as ingredient_ParentLot,
        level as sortorder
        from vw_trc_results
        {strwheretrc}
        """
    if GenOrTrc == "gen" or GenOrTrc == "all":
        qrystrGen = f"""select 'Gen' as type, 
        root_itemcode as root_itemcode,
        root_parentlot as root_parentlot,
        root_lot as root_lot,
        'NA' as root_supplierlot,
        level,
        product_itemcode as product_itemcode,
        product_lot as product_lot,
        Product_PLN as product_parentlot,
        ingredient_itemcode as ingredient_itemcode,
        ingredient_lot as ingredient_lot,
        supplierlot as ingredient_supplierlot ,
        ingredient_pln as ingredient_ParentLot,
        level * -1 as sortorder
        from vw_gen_results
        {strwheregen}
        """

    if qrystrGen != "" and qrystrTrc != "":
        qrystr = f"""
        select * from ({qrystrGen} union all by name {qrystrTrc}) as t
        """
    elif qrystrGen != "" and qrystrTrc == "":
        qrystr = qrystrGen
    elif qrystrGen == "" and qrystrTrc != "":
        qrystr = qrystrTrc
    else:
        raise ValueError("No query to execute. Please check the input parameters.")
    
    # Apply Product Code filter if provided
    product_code_filter = ""
    if product_code:
        product_code_filter = f"WHERE im_product.ProductCode = '{product_code}' OR im_ingredient.ProductCode = '{product_code}'"

    qrystr = f"""
            select *, 
            from ({qrystr}) as t
            LEFT JOIN ItemMaster im_root ON im_root.ItemCode = t.root_itemcode
            LEFT JOIN ItemMaster im_product ON im_product.ItemCode = t.product_itemcode
            LEFT JOIN ItemMaster im_ingredient ON im_ingredient.ItemCode = t.ingredient_itemcode
            {product_code_filter}
        """

    # Dynamic output columns handling
    if outputcols == "default" or outputcols is None:
        return engine.query(qrystr).pl()
    elif "exclude" in outputcols.lower():
        return engine.query(f"""
        select 
        {qrystr} 
        from ({qrystr}) as t
        group by product_name
        """).pl()
    else:
        return engine.query(f"""
        select {outputcols}, count(*) as CntRecs} 
        from ({qrystr}) as t
        group by product_name
        """).pl()

def func_trc_PrBID(level):
    engine.execute(
        """
        CREATE OR REPLACE TEMP TABLE vw_TrcProducts AS 
        select 
            PRODUCTBATCHID, p.Lot_Number, p.ItemCode, mt.SLNADJ, mt.PLN
        from tmp_products p
            JOIN vw_trc_items mt ON p.ItemCode = mt.ItemCode
        WHERE 1=1 AND mt.Type == 'Ingredient' 
        AND p.LotNumber == mt.LOT_NUMBER 
        GROUP BY ProductBatchID, p.Lot_Number, p.Name, mt.slnadj, mt.label
        """
    )

    engine.execute(
        f"""
        SELECT recursive 
        r as
    (
        select 
        C.ProductBatchID, 
        null as IngredientBatch,
        CAST('NACHOR' as productcode, 
        CAST('NACHOR') as Lot_Number, 
        1 as Level, 
        C.Lot_Number as Parent,
        C.itemcode as ParentItemCode,
        C.SLNADJ, 
        C.PLN ParentPLN
        from vw_Trc_PrBID C
        GROUP BY C.ProductBatchID, C.LOT_NUMBER, C.ItemCode, 
        C.SLNADJ, C.PLN				


        union all 

        select 
        d.ProductBatchID, 
        d.IngredientBatch, 
        CAST(d.ItemCode as productcode),
        CAST(d.LOT_NUMBER as productcode),
        r.Level + 1,
        r.Parent,
        r.ParentItemCode,
        R.SLNADJ,
        R.ParentPLN
        from r, pbid d 
        where 
        r.ProductBatchID = d.IngredientBatch 
        AND r.level< {level}
        )
        select * from r
        """
    )

    engine.execute(
        """
        CREATE OR REPLACE TEMP VIEW vw_Trc_Results AS
        with
            d
            AS
            (
                select 
                    PLN, 
                    BATCH_ID, 
                    TYPE, 
                    ItemCode, 
                    LOT_NUMBER,
                    SLNADJ as SupplierLot,
                    LotLabel,
                    ParentLotLabel
                from vw_MatTxnsWithItemCodes
                GROUP BY ALL
        ) ,
            bid
            as
            (
                SELECT 
                    l.ProductBatchID, 
                    l.IngredientBatchID, 
                    l.Level, 
                    ParentItemCode AS Root_ItemCode, 
                    Parent as Root_Lot,
                    'L' as Mode,
        		    ParentPLN as Root_ParentLot, 
        		    SLNADJ as Root_SupplierLot
                FROM tmp_Trc_Results_bid l
                WHERE 1=1 
                GROUP BY ALL
            )   
            , r as
        (
        SELECT
            bid.Root_ItemCode, 
            bid.Root_Lot, 
            bid.Level,
            bid.Root_ParentLot, 
            bid.Root_SupplierLot,
            p.BATCH_ID Product_BatchID, 
            p.ItemCode Product_ItemCode,
            p.LOT_NUMBER Product_Lot,
            p.PLN Product_PLN,
            p.LotLabel Product_LotLabel,
            p.ParentLotLabel Product_ParentLotLabel,
            i.BATCH_ID Ingredient_BatchID, 
            i.ItemCode Ingredient_ItemCode,
            i.LOT_NUMBER Ingredient_Lot,
            i.SupplierLot Ingredient_SupplierLot,
            i.pln Ingredient_PLN,
            i.LotLabel Ingredient_LotLabel,
            i.ParentLotLabel Ingredient_ParentLotLabel

        FROM bid
            LEFT OUTER JOIN d p ON bid.ProductBatchID = p.BATCH_ID AND p.TYPE = 'Product'
            LEFT OUTER JOIN d i ON bid.IngredientBatchID = i.BATCH_ID AND i.TYPE = 'Product'
        WHERE 1=1  
        GROUP BY ALL
        )
        select *
        from r
        """
    )


def func_gen_PrBID(level):
    engine.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE tmp_Gen_Results_bid AS
        with recursive
            pbid
            as
            (
                select ProductBatchID, IngredientBatchID
                from vw_Gen_PIBID 
                GROUP BY ALL
            ),
            r
            as
            (
                select
                    PBID.ProductBatchID,
                    IngredientBatchID,
                    1 as Level,
                    PBID.ProductBatchID as Parent,
    				C.NodeType
                FROM pbid
    				JOIN tmp_GenForLots C ON PBID.ProductBatchID = C.BATCH_ID
                WHERE 1=1

            UNION ALL

                select
                    d.ProductBatchID,
                    d.IngredientBatchID,
                    r.Level + 1,
                    r.Parent,
       				R.NodeType
                FROM r, pbid d
                WHERE 
    		r.IngredientBatchID = d.ProductBatchID
    		AND r.level< {level}
            )
        SELECT productbatchid, ingredientbatchid, level, parent, NodeType
        FROM r
        GROUP BY ALL;
    """
    )

    engine.execute(
        """
        CREATE OR REPLACE TEMP VIEW vw_Gen_Results AS 
        WITH
            d
            AS
            (
            SELECT 
                PLN, 
                BATCH_ID, 
                TYPE, 
                ItemCode, 
                LOT_NUMBER,
        		SLNADJ AS SupplierLot,
                LotLabel,
                ParentLotLabel
            FROM vw_MatTxnsWithItemCodes
            GROUP BY ALL
            ),
            bid
            AS
            (
                SELECT
                    l.ProductBatchID, 
                    l.Level, 
                    d.ItemCode ParentItemCode, 
                    d.PLN ParentLot ,
                    d.lot_number,
        			l.Parent ParentBatchID
                FROM tmp_Gen_Results_bid l
                    JOIN d ON l.Parent = d.BATCH_ID AND d.TYPE = 'Product'
                WHERE 1=1
                AND EXISTS (SELECT 1 FROM tmp_GenForLots f WHERE f.lot_number = d.lot_number)
                GROUP BY ALL
            ),
            r
            AS
            (
            SELECT
                    bid.ParentItemCode Root_ItemCode, 
                    bid.ParentLot Root_ParentLot, 
                    bid.lot_number Root_Lot,
                    bid.Level,
                    p.BATCH_ID Product_BatchID,
                    p.ItemCode Product_ItemCode,
                    p.PLN Product_PLN,
                    i.ItemCode Ingredient_ItemCode,
                    p.LOT_NUMBER Product_Lot,
                    p.LotLabel Product_LotLabel,
                    p.ParentLotLabel Product_ParentLotLabel,
                    i.BATCH_ID Ingredient_BatchID,
                    i.LOT_NUMBER Ingredient_Lot,
        			i.SupplierLot,
                    i.PLN Ingredient_PLN,
                    i.LotLabel Ingredient_LotLabel,
                    i.ParentLotLabel Ingredient_ParentLotLabel

            FROM bid
                    JOIN d p ON bid.ProductBatchID = p.BATCH_ID 
                        AND p.TYPE = 'Product'
                    JOIN d i ON bid.ProductBatchID = i.BATCH_ID 
                        AND i.TYPE = 'Ingredient'

            WHERE 
                (bid.level>1)
                OR (bid.level = 1 AND bid.lot_number = p.LOT_NUMBER)
            )
        SELECT *
        FROM r
    """
    )


def func_Source(input, GenOrTrc, level):
    varTraceFor = input

    if GenOrTrc == "trc" or GenOrTrc == "all":
        strTraceFor = f"""CREATE OR REPLACE TEMP TABLE tmp_TraceForLots AS (
                    SELECT mt.ItemCode, mt.Lot_Number, 'Lot' AS nodetype
                    FROM 
                    vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.LOT_NUMBER IN ('{varTraceFor}')
                        AND mt.TYPE = 'Ingredient' 
                    GROUP BY mt.ItemCode, mt.Lot_Number

                    UNION ALL

                    SELECT mt.ItemCode, mt.Lot_Number, 'ParentLot' AS nodetype
                    FROM 
                    vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.parent_lot_number IN ('{varTraceFor}')
                        AND mt.TYPE = 'Ingredient' 
                    GROUP BY mt.ItemCode, mt.Lot_Number

                    UNION ALL

                    SELECT mt.ItemCode, mt.LOT_NUMBER, 'Item' AS nodetype
                    FROM vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.itemcode IN ('{varTraceFor}')
                        AND mt.TYPE = 'Ingredient'
                    GROUP BY mt.ItemCode, mt.Lot_Number

                    UNION ALL

                    SELECT mt.ItemCode, mt.LOT_NUMBER, 'SupplierLot' AS nodetype
                    FROM 
                        vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.TYPE = 'Ingredient'
                        AND mt.SUPPLIER_LOT_NUMBER IN ('{varTraceFor}')
                    GROUP BY mt.ItemCode, mt.Lot_Number)
            """
        engine.execute(strTraceFor)
        func_trc_PrBID(level)

    if GenOrTrc == "gen" or GenOrTrc == "all":
        strGenFor = f"""CREATE OR REPLACE TEMP TABLE tmp_GenForLots AS (
                    SELECT mt.ItemCode, mt.Lot_Number, 'Lot' AS nodetype, BATCH_ID
                    FROM 
                    vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.LOT_NUMBER IN ('{varTraceFor}')
                        AND mt.TYPE = 'Product' 
                    GROUP BY ALL

                    UNION ALL

                    SELECT mt.ItemCode, mt.Lot_Number, 'ParentLot' AS nodetype, BATCH_ID
                    FROM 
                    vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.parent_lot_number IN ('{varTraceFor}')
                        AND mt.TYPE = 'Product' 
                    GROUP BY ALL

                    UNION ALL

                    SELECT mt.ItemCode, mt.LOT_NUMBER, 'Item' AS nodetype, BATCH_ID
                    FROM vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.itemcode IN ('{varTraceFor}')
                        AND mt.TYPE = 'Product'
                    GROUP BY ALL
                    )
            """
        engine.execute(strGenFor)
        func_gen_PrBID(level)


def func_Target(input):
    varTraceTarget = input

    strTraceTarget = f"""CREATE OR REPLACE TEMP TABLE tmp_TraceTarget AS (
        SELECT mt.ItemCode, mt.Lot_Number, 'Lot' AS nodetype
        FROM 
        vw_MatTxnsWithItemCodes mt
        WHERE 1=1 
            AND mt.LOT_NUMBER IN ('{varTraceTarget}')
            AND mt.TYPE = 'Ingredient' 
        GROUP BY mt.ItemCode, mt.Lot_Number

        UNION ALL

        SELECT mt.ItemCode, mt.Lot_Number, 'ParentLot' AS nodetype
        FROM 
        vw_MatTxnsWithItemCodes mt
        WHERE 1=1 
            AND mt.parent_lot_number IN ('{varTraceTarget}')
            AND mt.TYPE = 'Ingredient' 
        GROUP BY mt.ItemCode, mt.Lot_Number

        UNION ALL

        SELECT mt.ItemCode, mt.LOT_NUMBER, 'Item' AS nodetype
        FROM vw_MatTxnsWithItemCodes mt
        WHERE 1=1 
            AND mt.itemcode IN ('{varTraceTarget}')
            AND mt.TYPE = 'Ingredient'
        GROUP BY mt.ItemCode, mt.Lot_Number

        UNION ALL

        SELECT mt.ItemCode, mt.LOT_NUMBER, 'SupplierLot' AS nodetype
        FROM 
            vw_MatTxnsWithItemCodes mt
        WHERE 1=1 
            AND mt.TYPE = 'Ingredient'
            AND mt.SUPPLIER_LOT_NUMBER IN ('{varTraceTarget}')
        GROUP BY mt.ItemCode, mt.Lot_Number)
        """
    engine.execute(strTraceTarget)
