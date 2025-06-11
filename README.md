Now I want a new filter above Select Item Codes part which is also a dropdown. But in this I want all the distinct Product codes. So for this write a function in Lineage.py to get distinct Productcodes and then make changes to the frontend. So, when a user without selecting this dropdown, the app will work as it is, but when selected a value from this filter then provide the filtered output

Database result: shape: (2_060, 16)
┌──────┬────────────────┬───────────────┬───────────────┬───┬─────────────────────────────────┬─────────────────────────────────┬─────────┬───────────┐
│ type ┆ root_parentlot ┆ root_itemcode ┆ startnode     ┆ … ┆ ProductDescription              ┆ IngredientDescription           ┆ CntRecs ┆ CntRecs_1 │
│ ---  ┆ ---            ┆ ---           ┆ ---           ┆   ┆ ---                             ┆ ---                             ┆ ---     ┆ ---       │
│ str  ┆ str            ┆ str           ┆ str           ┆   ┆ str                             ┆ str                             ┆ i64     ┆ i64       │
╞══════╪════════════════╪═══════════════╪═══════════════╪═══╪═════════════════════════════════╪═════════════════════════════════╪═════════╪═══════════╡
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ B0101-19108   ┆ … ┆ BFR NACL 2M                     ┆ WEIGH KIT OF 2M SODIUM CHLORID… ┆ 4       ┆ 4         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ B0673WK-20210 ┆ … ┆ KIT BFR ACIDIFIED 20 PRCNT ETO… ┆ SODIUM ACETATE TRI-HYDRATE USP  ┆ 4       ┆ 4         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ B0101-19108   ┆ … ┆ BFR NACL 2M                     ┆ TUBING ASSEMBLY 1 IN ID EXTENS… ┆ 4       ┆ 4         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ C0624-20115A  ┆ … ┆ PRODUCTION OF RHASB IN THE GAL… ┆ BPC: 200L UNIVERSAL             ┆ 120     ┆ 120       │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ C71221-20113  ┆ … ┆ ASB BRX HRVST RDY CELL CULT     ┆ MEDIA PRODUCTION ACF RHASB      ┆ 4       ┆ 4         │
│ …    ┆ …              ┆ …             ┆ …             ┆ … ┆ …                               ┆ …                               ┆ …       ┆ …         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ B0666WK-20134 ┆ … ┆ WEIGH KIT 20 MM SODIUM ACETATE… ┆ SODIUM CHLORIDE, USP            ┆ 4       ┆ 4         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ B0656-20162   ┆ … ┆ BFR SANI II 0.5N NAOH           ┆ TUBING ASSEMBLY 1 IN ID EXTENS… ┆ 4       ┆ 4         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ M0612-20269   ┆ … ┆ MEDIA PRODUCTION ACF RHASB      ┆ MEDIA EX-CELL 302 ACF           ┆ 4       ┆ 4         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ M0612-20251   ┆ … ┆ MEDIA PRODUCTION ACF RHASB      ┆ TUBING: CLEAR C-FLEX IP #82     ┆ 4       ┆ 4         │
│ Gen  ┆ P0607B-20132   ┆ P0607B        ┆ P0604-20162   ┆ … ┆ RHASB:  BLUE SEPHAROSE FF CHRO… ┆ COLUMN PACKING: BLUE SEPHAROSE… ┆ 4       ┆ 4         │
└──────┴────────────────┴───────────────┴───────────────┴───┴─────────────────────────────────┴─────────────────────────────────┴─────────┴───────────┘
Columns: ['type', 'root_parentlot', 'root_itemcode', 'startnode', 'product_itemcode', 'endnode', 'ingredient_itemcode', 'Level', 'ParentName', 'ProductName', 'IngredientName', 'ParentDescription', 'ProductDescription', 'IngredientDescription', 'CntRecs', 'CntRecs_1']
Error getting lineage data: name 'engine' is not defined
No data provided to tree chart
            
