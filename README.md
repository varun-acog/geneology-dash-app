
My dash app:

Now in the filters section, I have a dropdown above Select Product Code called "What are you looking for?" and this dropdown should have these items:

Everything went into making the Lot/Item (when this is selected, only Genealogy check box should be checked)

Link between the two Lots(when this is selected both Genealogy and Traceability checkboxes should be checked)

Where the Lot got Used/Consumed(when this is selected, only Traceability check box should be checked)

Where Used(Put it as it is for now no functionality)

In the callback for output(s): product-codes-dropdown.value item-codes-dropdown.value data-table.rowData@307b61fbf4f3aae5ecf09f88b4f7760fa7455969a6bc5727b1efdd0ad0e13006 all-data-store.data@307b61fbf4f3aae5ecf09f88b4f7760fa7455969a6bc5727b1efdd0ad0e13006 filtered-data-store.data@307b61fbf4f3aae5ecf09f88b4f7760fa7455969a6bc5727b1efdd0ad0e13006 unit-operation-dropdown.value attribute-dropdown.value gen-trc-checklist.value lookup-type-dropdown.value Output 7 (gen-trc-checklist.value) is already in use. To resolve this, set `allow_duplicate=True` on duplicate outputs, or combine the outputs into one callback function, distinguishing the trigger by using `dash.callback_context` if necessary.
