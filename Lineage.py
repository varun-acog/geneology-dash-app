import duckdb
import polars as pl

# import json

# Author: Satish Vammi
# Description: This script is used to create a traceability and genealogy system using DuckDB.
# Function accepts Item codes, Lot Numbers, Parent Lot or Supplier Lot Numbers as source and target.
# It creates temporary tables to store the results of the traceability and genealogy queries in-memory so the output is session scoped
# To-do: Add more comments and docstrings to the code. Add more test cases to the test function.
# To-do: Add function to output visualization of the data

DATABASE_URL =  r"data/lineage.db"

engine = duckdb.connect(DATABASE_URL, read_only=True)

__all__ = ["get_lineage"]




def get_item_codes(search_value) -> list[str]:
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
):
    """
    Function to get the results of the query in the specified format.
    :param startNodes: list of Item codes, Lot Numbers, Parent Lot or Supplier Lot Numbers to trace.
    :param endNodes: list of Item codes, Lot Numbers, Parent Lot to target.
    :param outputtype: The output type, either 'polars' or 'duckdb'.
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
    
    qrystr = f"""
            select *, im_root.UnitOpName as root_unit_op_name,
            im_root.Description as root_description,
            im_product.UnitOpName as product_unit_op_name,
            im_product.Description as product_description,
            im_ingredient.UnitOpName as ingredient_unit_op_name,
            im_ingredient.Description as ingredient_description
            from ({qrystr}) as t
            LEFT JOIN ItemMaster as im_root ON im_root.ItemCode = t.root_itemcode
            LEFT JOIN ItemMaster as im_product ON im_product.ItemCode = t.product_itemcode
            LEFT JOIN ItemMaster as im_ingredient ON im_ingredient.ItemCode = t.ingredient_itemcode
        """

    # Dynamic output columns handling
    if outputcols == "default" or outputcols is None:
        qrystr = qrystr
    elif "exclude" in outputcols.lower():
        qrystr = f"""
        select * {outputcols}, count(*) as CntRecs from ({qrystr}) as t
        group by all
        """
    else:
        qrystr = f"""
        select {outputcols}, count(*) as CntRecs from ({qrystr}) as t
        group by all
        """
    

    if outputtype == "polars":
        return engine.execute(qrystr).pl()
    elif (
        outputtype == "duckdb"
    ):  # this is returning a tuple, not exactly a duckdb dataframe
        # return engine.sql(qrystr).execute()
        return engine.execute(qrystr).fetchall()
    # elif outputtype == "csv":
    else:
        raise ValueError("Invalid output type. Use 'polars' or 'duckdb'.")

    # engine.close()


def func_trc_PrBID(level):
    engine.execute(
        """
        CREATE OR REPLACE TEMP TABLE vw_Trc_PrBID AS 
        select 
            PRODUCTBATCHID, p.Lot_Number, p.ItemCode, mt.SLNADJ, mt.PLN
        from tmp_TraceForLots p
            JOIN vw_trc_PIBID mt on p.ItemCode = mt.ItemCode
        WHERE 1=1 AND mt.Type='Ingredient' 
        AND p.lot_number = mt.LOT_NUMBER 
        --AND P.NodeType <> 'ParentLot' 		
        group by ProductBatchID, p.Lot_Number, p.ItemCode, mt.slnadj, mt.pln
        """
    )

    #     union all

    # select
    #     PRODUCTBATCHID, p.Lot_Number, p.ItemCode, mt.SLNADJ, mt.PLN
    # from tmp_TraceForLots p
    #     JOIN vw_trc_PIBID mt on p.ItemCode = mt.ItemCode
    # WHERE 1=1 AND mt.Type='Ingredient'
    # AND p.lot_number = mt.PLN AND P.NodeType = 'ParentLot'
    # group by ProductBatchID, p.Lot_Number, p.ItemCode, mt.SLNADJ, mt.PLN

    engine.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE tmp_Trc_Results_bid AS
        with recursive 
        pbid as
    (
        select ProductBatchID, IngredientBatchID, ItemCode, Lot_Number
        from vw_trc_PIBID
    )
    ,
    r as
    (
        select 
        C.ProductBatchid, 
        null as IngredientBatchID,
        CAST('NANCHOR' as nvarchar(50)) AS ItemCode, 
        CAST('NANCHOR' as nvarchar(50)) AS Lot_Number, 
        --ingredient batchid not required for traceability
        --IngredientBatchID, 
        --pbid.ItemCode,
        --pbid.LOT_NUMBER,
        1 as Level, 
        C.Lot_Number as Parent,
        C.itemcode as ParentItemCode,
        --C.PROJECTID, 
        --C.RecID, 
        C.SLNADJ, 
        C.PLN ParentPLN
        from vw_Trc_PrBID C
        GROUP BY C.ProductBatchID, C.LOT_NUMBER, C.ItemCode, 
        --C.Projectid, C.RecID, 
        C.SLNADJ, C.PLN				


        union all 

        select 
        d.ProductBatchID, 
        d.IngredientBatchID, 
        CAST(d.ItemCode as nvarchar(50)) AS ItemCode,
        CAST(d.LOT_NUMBER as nvarchar(50)) AS LOT_NUMBER,
        r.Level + 1,
        r.Parent,
        r.ParentItemCode,
        --R.PROJECTID, 
        --R.RecID,
        R.SLNADJ,
        R.ParentPLN
        from r, pbid d 
        where 
        r.ProductBatchID = d.IngredientBatchID 
        --to prevent from failing as the max recursion is 100
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
                --TODO Get Item Master and Lot Number
                --Avoid Transaction Table 
                select 
                    PLN, 
                    BATCH_ID, 
                    --SUM(QUANTITY) TotalQty, 
                    TYPE, 
                    ItemCode, 
                    --TRANSACTION_UOM,
                    --MIN(TRANSACTION_DATE) MINTXNDATE,
                    --MAX(TRANSACTION_DATE) MAXTXNDATE, COUNT(*) CNT,
                    --ProductCode,
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
            LEFT OUTER JOIN d p on bid.ProductBatchID = p.BATCH_ID AND p.TYPE = 'Product'
            LEFT OUTER JOIN d i on bid.IngredientBatchID = i.BATCH_ID and i.TYPE = 'Product'
        WHERE 1=1  
        GROUP BY ALL
        )
        select *
        -- ParentItemCode, 
        -- ParentLot, 
        -- ParentPLN,
        -- ParentSuppLN,
        -- Level, 
        -- ProductBatchID, 
        -- ProductItemCode, 
        -- ProductLot,
        -- ProductLotPLN,
        -- IngBatchID,
        -- CASE WHEN IngredientItemCode IS NULL THEN ParentItemCode ELSE IngredientItemCode END AS IngredientItemCode,
        -- case when IngredientLot is null then ParentLot else IngredientLot end as IngredientLot
        from r
        """
    )


def func_gen_PrBID(level):
    # This is where the recursion happens to link the child nodes to root node
    engine.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE tmp_Gen_Results_bid AS
        with recursive
            pbid
            as
            (
                select ProductBatchID, IngredientBatchID
                from vw_Gen_PIBID 
                GROUP BY all
            ),
            r
            as
            (
                select
                    PBID.ProductBatchid,
                    IngredientBatchID,
                    1 as Level,
                    PBID.ProductBatchID as Parent,
    				C.NodeType
                from pbid
    				JOIN tmp_GenForLots C ON PBID.ProductBatchID = C.BATCH_ID
                where 1=1

            union all

                select
                    d.ProductBatchID,
                    d.IngredientBatchID,
                    r.Level + 1,
                    r.Parent,
       				R.NodeType
                from r, pbid d
                where 
    		--use below for finding ancestors i.e., top (final goods) to bottom
    		r.IngredientBatchID = d.ProductBatchID
    		AND r.level< {level}
            )
        select productbatchid, ingredientbatchid, level, parent, NodeType
        from r
        group by all;
    """
    )

    engine.query(
        """
        CREATE OR REPLACE TEMP VIEW vw_Gen_Results AS 
        with
            d
            AS
            (
            select 
                PLN, 
                BATCH_ID, 
                --SUM(QUANTITY) TotalQty, 
                TYPE, 
                ItemCode, 
                --TRANSACTION_UOM,
                --MIN(TRANSACTION_DATE) MINTXNDATE,
                --MAX(TRANSACTION_DATE) MAXTXNDATE, COUNT(*) CNT,
                --ProductCode,
                --ItemType, 
                LOT_NUMBER,
        		SLNADJ as SupplierLot,
                LotLabel,
                ParentLotLabel
            from vw_MatTxnsWithItemCodes
            GROUP BY all
            ),
            bid
            as
            (
                SELECT
                    l.ProductBatchID, 
                    l.Level, 
                    d.ItemCode ParentItemCode, 
                    d.PLN ParentLot ,
                    d.lot_number,
                    --d.ProductCode ParentProductCode,
        			l.Parent ParentBatchID
                FROM tmp_Gen_Results_bid l
                    JOIN d on l.Parent = d.BATCH_ID and d.type = 'Product'
                WHERE 1=1
                AND EXISTS (SELECT 1 from tmp_GenForLots f where f.lot_number = d.lot_number)
                GROUP BY all
            ),
            r
            as
            (
            SELECT
        		    --bid.ParentBatchID,
                    --bid.ParentProductCode Root_ProductCode,
                    bid.ParentItemCode Root_ItemCode, 
                    bid.ParentLot Root_ParentLot, 
                    bid.lot_number Root_Lot,
                    bid.Level,
                    --i.itemtype,
                    p.BATCH_ID Product_BatchID,
                    p.ItemCode Product_ItemCode,
                    p.PLN Product_PLN,
                    i.ItemCode Ingredient_ItemCode,
                    --i.PLN IngredientLot,
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
                    JOIN d p on bid.ProductBatchID = p.BATCH_ID 
                        AND p.TYPE = 'Product'
                    JOIN d i on bid.ProductBatchID = i.BATCH_ID 
                        and i.TYPE = 'Ingredient'

            WHERE 
                (bid.level>1)
                OR (bid.level = 1 AND bid.lot_number = p.LOT_NUMBER)
            )
        select *
        from r
    """
    )


def func_Source(input, GenOrTrc, level):
    # This function converts Item Code, Lot Number, Parent Lot and Supplier Lot into Batch ID's for Gen and Lots for Trace.
    # Creates temporary tables based on the input Item codes, Lot Numbers, Parent Lot or Supplier Lot Numbers.
    varTraceFor = input

    if GenOrTrc == "trc" or GenOrTrc == "all":
        strTraceFor = f"""CREATE OR REPLACE TEMP TABLE tmp_TraceForLots AS (
                    select mt.ItemCode, mt.Lot_Number, 'Lot' as nodetype
                    from 
                    vw_MatTxnsWithItemCodes mt
                    where 1=1 
                        AND mt.LOT_NUMBER in ('{varTraceFor}')
                        AND mt.type = 'Ingredient' 
                    group by mt.ItemCode, mt.Lot_Number

                    union all

                    select mt.ItemCode, mt.Lot_Number,  'ParentLot' as nodetype
                    from 
                    vw_MatTxnsWithItemCodes mt
                    where 1=1 
                        AND mt.parent_lot_number in ('{varTraceFor}')
                        AND mt.type = 'Ingredient' 
                    group by mt.ItemCode, mt.Lot_Number

                    union all

                    select mt.ItemCode,  mt.LOT_NUMBER,  'Item' as nodetype
                    from vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.itemcode in ('{varTraceFor}')
                        AND mt.type = 'Ingredient'
                    group by mt.ItemCode, mt.Lot_Number

                    union all

                    select mt.ItemCode,  mt.LOT_NUMBER,  'SupplierLot' as nodetype
                    from 
                        vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.TYPE = 'Ingredient'
                        AND mt.SUPPLIER_LOT_NUMBER in ('{varTraceFor}')
                    group by mt.ItemCode, mt.Lot_Number)
            """
        engine.execute(strTraceFor)
        func_trc_PrBID(level)  # refresh trace temp tables

    if GenOrTrc == "gen" or GenOrTrc == "all":
        strGenFor = f"""CREATE OR REPLACE TEMP TABLE tmp_GenForLots AS (
                    select mt.ItemCode,  mt.Lot_Number,  'Lot' as nodetype, BATCH_ID
                    from 
                    vw_MatTxnsWithItemCodes mt
                    where 1=1 
                        AND mt.LOT_NUMBER in ('{varTraceFor}')
                        AND mt.type = 'Product' 
                    group by all

                    union all

                    select mt.ItemCode,  mt.Lot_Number,  'ParentLot' as nodetype, BATCH_ID
                    from 
                    vw_MatTxnsWithItemCodes mt
                    where 1=1 
                        AND mt.parent_lot_number in ('{varTraceFor}')
                        AND mt.type = 'Product' 
                    group by all

                    union all

                    select mt.ItemCode,  mt.LOT_NUMBER,  'Item' as nodetype, BATCH_ID
                    from vw_MatTxnsWithItemCodes mt
                    WHERE 1=1 
                        AND mt.itemcode in ('{varTraceFor}')
                        AND mt.type = 'Product'
                    group by all
                    )
            """
        # print(strGenFor)
        engine.execute(strGenFor)
        func_gen_PrBID(level)  # refresh gen temp tables


def func_Target(input):
    # This function converts Item Code, Lot Number, Parent Lot and Supplier Lot into Batch ID's for Gen and Lots for Trace.
    # Creates temporary tables based on the input Item codes, Lot Numbers, Parent Lot or Supplier Lot Numbers.
    varTraceTarget = input

    strTraceTarget = f"""CREATE OR REPLACE TEMP TABLE tmp_TraceTarget AS (
        select mt.ItemCode,  mt.Lot_Number,  'Lot' as nodetype
        from 
        vw_MatTxnsWithItemCodes mt
        where 1=1 
            AND mt.LOT_NUMBER in ('{varTraceTarget}')
            AND mt.type = 'Ingredient' 
        group by mt.ItemCode, mt.Lot_Number

        union all

        select mt.ItemCode,  mt.Lot_Number,  'ParentLot' as nodetype
        from 
        vw_MatTxnsWithItemCodes mt
        where 1=1 
            AND mt.parent_lot_number in ('{varTraceTarget}')
            AND mt.type = 'Ingredient' 
        group by mt.ItemCode, mt.Lot_Number

        union all

        select mt.ItemCode,  mt.LOT_NUMBER,  'Item' as nodetype
        from vw_MatTxnsWithItemCodes mt
        WHERE 1=1 
            AND mt.itemcode in ('{varTraceTarget}')
            AND mt.type = 'Ingredient'
        group by mt.ItemCode, mt.Lot_Number

        union all

        select mt.ItemCode,  mt.LOT_NUMBER,  'SupplierLot' as nodetype
        from 
            vw_MatTxnsWithItemCodes mt
        WHERE 1=1 
            AND mt.TYPE = 'Ingredient'
            AND mt.SUPPLIER_LOT_NUMBER in ('{varTraceTarget}')
        group by mt.ItemCode, mt.Lot_Number)
        """
    # print(str)
    engine.execute(strTraceTarget)
