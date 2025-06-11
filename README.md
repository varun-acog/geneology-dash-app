Database result: shape: (16, 6)
┌──────┬────────────────┬───────────┬──────────┬───────┬─────────┐
│ type ┆ root_parentlot ┆ startnode ┆ endnode  ┆ Level ┆ CntRecs │
│ ---  ┆ ---            ┆ ---       ┆ ---      ┆ ---   ┆ ---     │
│ str  ┆ str            ┆ str       ┆ str      ┆ i32   ┆ i64     │
╞══════╪════════════════╪═══════════╪══════════╪═══════╪═════════╡
│ Trc  ┆ A1276211       ┆ A1292970  ┆ A1275656 ┆ 3     ┆ 1       │
│ Trc  ┆ A1276211       ┆ A1275656  ┆ A1275880 ┆ 2     ┆ 1       │
│ Trc  ┆ A1276211       ┆ A1275640  ┆ A1275862 ┆ 3     ┆ 18      │
│ Trc  ┆ A1276211       ┆ A1275656  ┆ A1276211 ┆ 1     ┆ 1       │
│ Trc  ┆ A1276211       ┆ A1275862  ┆ A1275656 ┆ 2     ┆ 1       │
│ …    ┆ …              ┆ …         ┆ …        ┆ …     ┆ …       │
│ Trc  ┆ A1276211       ┆ A1292970  ┆ A1275656 ┆ 2     ┆ 1       │
│ Trc  ┆ A1276211       ┆ A1276098  ┆ A1292970 ┆ 4     ┆ 18      │
│ Trc  ┆ A1276211       ┆ A1275641  ┆ A1275863 ┆ 4     ┆ 17      │
│ Trc  ┆ A1276211       ┆ A1275862  ┆ A1275656 ┆ 3     ┆ 1       │
│ Trc  ┆ A1276211       ┆ A1275863  ┆ A1275656 ┆ 2     ┆ 1       │
└──────┴────────────────┴───────────┴──────────┴───────┴─────────┘
Columns: ['type', 'root_parentlot', 'startnode', 'endnode', 'Level', 'CntRecs']

- root_itemcode -> Parent Item Code
	- root_parentlot -> Parent Name
	- root_parentlot -> Parent PN
	- product_itemcode -> Product Item Code
	- startnode -> Product Name
	- startnode -> Product PN
	- level -> level
	- ingredient_itemcode -> Ingredient Item Code
	- endnode -> Ingredient Name
	- endnode -> Ingredient PN
	- CntRecs -> CntRecs


Database result: shape: (69, 15)
┌──────┬────────────────┬───────────────┬───────────────┬───┬─────────────────────────┬───────────────────────────┬──────────────────────────┬─────────┐
│ type ┆ root_parentlot ┆ root_itemcode ┆ startnode     ┆ … ┆ ParentDescription       ┆ ProductDescription        ┆ IngredientDescription    ┆ CntRecs │
│ ---  ┆ ---            ┆ ---           ┆ ---           ┆   ┆ ---                     ┆ ---                       ┆ ---                      ┆ ---     │
│ str  ┆ str            ┆ str           ┆ str           ┆   ┆ str                     ┆ str                       ┆ str                      ┆ i64     │
╞══════╪════════════════╪═══════════════╪═══════════════╪═══╪═════════════════════════╪═══════════════════════════╪══════════════════════════╪═════════╡
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ P12003A-20119 ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ CNP FBDS 8 MG/ML          ┆ CM Sepharose             ┆ 19      │
│      ┆                ┆               ┆               ┆   ┆                         ┆                           ┆ Chromatography El…       ┆         │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ P12003A-20121 ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ CNP FBDS 8 MG/ML          ┆ CM Sepharose             ┆ 23      │
│      ┆                ┆               ┆               ┆   ┆                         ┆                           ┆ Chromatography El…       ┆         │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ BOXG19B       ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ BMN111 1.2MG/VIAL NOV 402 ┆ CNP FBDS 8 MG/ML         ┆ 23      │
│      ┆                ┆               ┆               ┆   ┆                         ┆ RVS4                      ┆                          ┆         │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ BOXJ24A       ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ BMN111 0.40MG/VIAL NOV    ┆ CNP FBDS 8 MG/ML         ┆ 23      │
│      ┆                ┆               ┆               ┆   ┆                         ┆ 402 RVS…                  ┆                          ┆         │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ P12003A-20121 ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ CNP FBDS 8 MG/ML          ┆ CM Sepharose             ┆ 23      │
│      ┆                ┆               ┆               ┆   ┆                         ┆                           ┆ Chromatography El…       ┆         │
│ …    ┆ …              ┆ …             ┆ …             ┆ … ┆ …                       ┆ …                         ┆ …                        ┆ …       │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ L221978       ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ BMN111 209 10X 0.56MG/VL  ┆ BMN111 0.56MG/VL NOV 402 ┆ 1       │
│      ┆                ┆               ┆               ┆   ┆                         ┆                           ┆ 90k                      ┆         │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ P12003A-20122 ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ CNP FBDS 8 MG/ML          ┆ CM Sepharose             ┆ 24      │
│      ┆                ┆               ┆               ┆   ┆                         ┆                           ┆ Chromatography El…       ┆         │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ BOXK28A       ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ BMN111 0.56MG/VL NOV 402  ┆ CNP FBDS 8 MG/ML         ┆ 24      │
│      ┆                ┆               ┆               ┆   ┆                         ┆ 90k                       ┆                          ┆         │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ P2202-20122   ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ BMN111 SP SEPH ELUATE     ┆ 10 IN SUPOR UEAV FILTER  ┆ 1       │
│ Trc  ┆ Z1303-20113    ┆ Z1303         ┆ P2202-20120   ┆ … ┆ 10 IN SUPOR UEAV FILTER ┆ BMN111 SP SEPH ELUATE     ┆ 10 IN SUPOR UEAV FILTER  ┆ 1       │
└──────┴────────────────┴───────────────┴───────────────┴───┴─────────────────────────┴───────────────────────────┴──────────────────────────┴─────────┘
Columns: ['type', 'root_parentlot', 'root_itemcode', 'startnode', 'product_itemcode', 'endnode', 'ingredient_itemcode', 'Level', 'ParentName', 'ProductName', 'IngredientName', 'ParentDescription', 'ProductDescription', 'IngredientDescription', 'CntRecs']

6.1 : ADD LOADING OBHECT WHEREEVER QUERY USED.
7.  convert the column mapping   
    - root_itemcode -> Parent Item Code
	- ParentName -> Parent Name
	- root_parentlot -> Parent PN
	- product_itemcode -> Product Item Code
	- ProductName -> Product Name
	- startnode -> Product PN
	- level -> level
	- ingredient_itemcode -> Ingredient Item Code
	- IngredientName -> Ingredient Name
	- endnode -> Ingredient PN
	- CntRecs -> CntRecs

8. On the unit Operation dyanmaic dropdown show the unique list of all the root_parentlot, startnode, endnode and get the corresponding Names
   show the label as Lot - Name format
   product unit operation and ingredient unit operation and root unit operation
   product unit operation - product_itemocode + '-' + ProductName
   ingredient unit operation - ingredient_itemocode + '-' + IngredientName
   root unit operation - root_itemocode + '-' + ParentName
   
   get the unique values of all itemcode and show it as value and corresponding unit operation as label 
   

9. In the visualization on the tooltip show the Name and Description from the results.

Now, in the additional filters sections, we have unit operations. In this unit operations, we are having Product Item Codes as filtering options, but now make it as "Product Item Code-Product Name" and "Ingredient Item Code-Ingredient Name" for both products and ingredients respectively

