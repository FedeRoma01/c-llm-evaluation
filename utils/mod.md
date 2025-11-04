### Modularity
Evaluate whether the program is decomposed into clear, single-purpose functions. Identify duplicated logic, oversized functions, or unclear separation of concerns.

In the reference program:

- Each exam requirement is implemented in a separate function:
  `stampa_contrario`, `max_distribuzione`, `righe`, `stampa_min_max`, `stampa_somme`.
- The function `leggi_file` is solely responsible for reading and building the data structure, clearly separating input handling from computation.
- The `main` function coordinates execution without performing direct processing.
- Functions communicate exclusively through parameters (`struct file *dati`), without relying on global variables.
- The `leggi_file` function handles error messages and memory freeing internally and returns an error code, without propagating detailed error information.

**To achieve a full score (10/10):**
The program should consist of small, cohesive functions with descriptive names, clear interfaces, and distinct responsibilities. Each part of the problem must be encapsulated in a reusable, self-contained module that can be tested independently.
