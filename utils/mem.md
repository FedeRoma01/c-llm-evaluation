### Correct use of dynamic memory
Check that all dynamic allocations (malloc, realloc) are verified for success, properly freed, and used without invalid accesses or memory leaks.

In the reference program:

- The array of lines `dati->linee` is dynamically allocated with `malloc` and expanded using `realloc` as new data are read.
- Every allocation is checked for success (`if (tmp == NULL)` and `if (dati->linee == NULL)`), with memory safely freed upon failure (`free(dati->linee)`).
- The leggi_file function returns void and does not signal allocation failures to the caller.
- The final realloc in leggi_file function is not checked for failure.
- All allocated memory is correctly released at the end (`free(dati.linee)` in `main`).
- No redundant allocations or double frees are present.
- The final realloc occurs after all data are successfully read; failure at that point would not corrupt data or cause leaks.

**To achieve 10/10:**  
The code must demonstrate a complete and safe memory lifecycle — *allocation → use → possible reallocation → deallocation* — with systematic error checking, no memory leaks, and structural consistency between allocated data and program logic.
