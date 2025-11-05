### `modularity.c`: Modifications to Modularity

The file **`modularity.c`** sacrificed modularity by consolidating the program logic.

| Modified Aspect | Description of Change | Comparison with `soluzione.c` |
| :--- | :--- | :--- |
| **Modularity (Functions)** | All functionalities (file reading, points 1-5) were **embedded directly inside the `main()` function**. Auxiliary functions were removed, and their code was copied inline. | `soluzione.c` uses dedicated functions for file reading and for solving each of the 5 exam points, improving readability. |
| **Comparison Function** | The `cmp()` function for `qsort` is the only non-`main` function remaining. | `soluzione.c` also uses the `cmp()` function. |

---

### `dynamic_mem.c`: Modifications to Dynamic Memory Usage

The file **`dynamic_mem.c`** introduced errors in dynamic memory allocation and usage.

| Modified Aspect | Description of Change | Comparison with `soluzione.c` |
| :--- | :--- | :--- |
| **Initial Allocation** | In `leggi_file()`, the initial allocation is made for **only 1 byte** (`dati->linee = malloc(dimc);` where `dimc` is 1), ignoring the size of `struct linea`. | `soluzione.c` correctly allocates memory for the structure size: `dati->linee = malloc(dimc * sizeof(*(dati->linee)));`. |
| **Intermediate Reallocation** | In `leggi_file()`, the intermediate reallocation only reallocates **`dimc` bytes** (`dati->linee = realloc(dati->linee, dimc);`), failing to multiply by `sizeof(*(dati->linee))`. | `soluzione.c` correctly reallocates: `tmp = realloc(dati->linee, dimc * sizeof(*(dati->linee)));`. |
| **Final Reallocation** | In `leggi_file()`, the final resizing is incorrect: `dati->linee = realloc(dati->linee, dati->n);`, reallocating for **`dati->n` bytes** instead of `dati->n` *structures*. | `soluzione.c` correctly reallocates: `tmp = realloc(dati->linee, dati->n * sizeof(*(dati->linee)));`. |
| **Memory Deallocation** | The call to `free(dati.linee)` is **missing** in `main()`. | `soluzione.c` frees the memory with `free(dati.linee)`. |

---

### `errors.c`: Modifications to Error Handling and Robustness

The file **`errors.c`** removed or altered essential error checks, making the code less robust.

| Modified Aspect | Description of Change | Comparison with `soluzione.c` |
| :--- | :--- | :--- |
| **`argc` Check** | The check for the correct number of command-line arguments is completely **missing** in `main()`. | `soluzione.c` verifies `if (argc != 2)` and exits if incorrect. |
| **`fopen` Verification** | The `main()` function **does not check** the return value of `fopen()`. | `soluzione.c` checks `if ((f = fopen(argv[1], "r")) == NULL)` and handles the error. |
| **`malloc` Verification** | In `leggi_file()`, the check for the success of the initial `malloc` allocation is **omitted**. | `soluzione.c` checks `if (dati->linee == NULL)` to handle allocation failure. |
| **`realloc` Verification** | In `leggi_file()`, checks for `realloc` success and the use of a temporary pointer are **omitted**. The assignment is direct. | `soluzione.c` uses a temporary pointer `tmp` and verifies `if (tmp == NULL)`. |
| **`sscanf` Check** | In `leggi_file()`, the return value of `sscanf` is **not checked**. All data is processed, even if a line doesn't contain 10 numbers. | `soluzione.c` verifies `if (numbers == 10)` and ignores non-conforming lines. |

---

### `data_struct.c`: Modifications to Data Structures and Constants

The file **`data_struct.c`** contains changes that make the data structures and related algorithms inconsistent.

| Modified Aspect | Description of Change | Comparison with `soluzione.c` |
| :--- | :--- | :--- |
| **Row Size (`NNUM`)** | The constant `NNUM` was **reduced to `(2)`**. | `soluzione.c` defines `NNUM` as `(10)`. |
| **Data Reading** | `sscanf` in `leggi_file()` still attempts to read **10 numbers**, but the destination array size is only `NNUM=2`. | `soluzione.c` reads 10 numbers into an array of size 10. |
| **Sum Calculation** | The loop for calculating the sum iterates over `NNUM=2` elements, **not the 10** numbers that `sscanf` attempts to read. | `soluzione.c` iterates over `NNUM=10` for the sum. |
| **Histogram Size (Point 2)** | The `istogramma` array in `max_distribuzione()` was **reduced to size `[10]`** instead of `[201]` (required for the $\left[-100, 100\right]$ range). | `soluzione.c` uses `int istogramma[201] = {0}`. |
| **Histogram Iteration** | The loops for finding the maximum frequency and printing the results iterate over **10 elements** instead of 201. | `soluzione.c` iterates over 201 elements. |