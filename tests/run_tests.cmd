
set test_files=(shared_utils options)

for %%n in %test_files% do (
    python tests\%%n_test.py
)
