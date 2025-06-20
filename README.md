
My dash app:

Now in the filters section, I have a dropdown above Select Product Code called "What are you looking for?" and this dropdown should have these items:

Everything went into making the Lot/Item (when this is selected, only Genealogy check box should be checked)

Link between the two Lots(when this is selected both Genealogy and Traceability checkboxes should be checked)

Where the Lot got Used/Consumed(when this is selected, only Traceability check box should be checked)

Where Used(Put it as it is for now no functionality)

Traceback (most recent call last):
  File "/home/users/pr912591/Lineage/Lineage/app.py", line 905, in <module>
    @app.callback(
     ^^^^^^^^^^^^^
  File "/bmrn/spack-packages/linux-rocky8-skylake_avx512/gcc-11.2.0/miniconda3-22.11.1-p72fec7kgbdrqs2wvagbhvlq3ixkdop7/envs/geneology/lib/python3.11/site-packages/dash/dash.py", line 1295, in callback
    return _callback.callback(
           ^^^^^^^^^^^^^^^^^^^
  File "/bmrn/spack-packages/linux-rocky8-skylake_avx512/gcc-11.2.0/miniconda3-22.11.1-p72fec7kgbdrqs2wvagbhvlq3ixkdop7/envs/geneology/lib/python3.11/site-packages/dash/_callback.py", line 205, in callback
    return register_callback(
           ^^^^^^^^^^^^^^^^^^
  File "/bmrn/spack-packages/linux-rocky8-skylake_avx512/gcc-11.2.0/miniconda3-22.11.1-p72fec7kgbdrqs2wvagbhvlq3ixkdop7/envs/geneology/lib/python3.11/site-packages/dash/_callback.py", line 348, in register_callback
    callback_id = insert_callback(
                  ^^^^^^^^^^^^^^^^
  File "/bmrn/spack-packages/linux-rocky8-skylake_avx512/gcc-11.2.0/miniconda3-22.11.1-p72fec7kgbdrqs2wvagbhvlq3ixkdop7/envs/geneology/lib/python3.11/site-packages/dash/_callback.py", line 264, in insert_callback
    _validate.validate_duplicate_output(
  File "/bmrn/spack-packages/linux-rocky8-skylake_avx512/gcc-11.2.0/miniconda3-22.11.1-p72fec7kgbdrqs2wvagbhvlq3ixkdop7/envs/geneology/lib/python3.11/site-packages/dash/_validate.py", line 586, in validate_duplicate_output
    _valid(output)
  File "/bmrn/spack-packages/linux-rocky8-skylake_avx512/gcc-11.2.0/miniconda3-22.11.1-p72fec7kgbdrqs2wvagbhvlq3ixkdop7/envs/geneology/lib/python3.11/site-packages/dash/_validate.py", line 573, in _valid
    raise exceptions.DuplicateCallback(
dash.exceptions.DuplicateCallback: allow_duplicate requires prevent_initial_call to be True. The order of the call is not guaranteed to be the same on every page load. To enable duplicate callback with initial call, set prevent_initial_call='initial_duplicate'  or globally in the config prevent_initial_callbacks='initial_duplicate'
(geneology) [pr912591@hpcapps Lineage]$ 
