/* Soluzione del tema d'esame del 2022-07-28 */

#include <stdio.h>
#include <stdlib.h>

#define NNUM (10) // numero di valori numerici per ogni riga

// struttura che rappresenta una riga del file
struct linea {
    int numeri[NNUM]; // i 10 numeri letti
    int somma;        // la somma dei 10 numeri
};

// struttura che rappresenta l'intero file
struct file {
    int n;               // numero di righe lette
    struct linea *linee; // puntatore alle righe
};

/* Funzione per leggere i dati dal file e salvarli nella struttura */
void leggi_file(FILE *f, struct file *dati)
{
    int dimc = 1, s, i;
    struct linea *linea;
    char buf[2048];
    
    dati->n = 0;
    // alloco inizialmente un solo byte, sarà sufficiente per cominciare
    dati->linee = malloc(dimc);

    while (fgets(buf, sizeof(buf), f)) {
        // assegno il puntatore alla prossima riga da leggere
        linea = dati->linee + dati->n;

        // leggo 10 interi da ogni riga
        int numbers = sscanf(buf, "%d %d %d %d %d %d %d %d %d %d",
                linea->numeri + 0,
                linea->numeri + 1,
                linea->numeri + 2,
                linea->numeri + 3,
                linea->numeri + 4,
                linea->numeri + 5,
                linea->numeri + 6,
                linea->numeri + 7,
                linea->numeri + 8,
                linea->numeri + 9);
        if (numbers == 10) {
            // calcolo la somma dei valori
            s = 0;
            for (i = 0; i < NNUM; ++i) {
                s += linea->numeri[i];
            }
            linea->somma = s;

            // incremento il numero di righe lette
            dati->n += 1;

            // raddoppio la capacità quando necessario
            if (dati->n >= dimc) {
                dimc *= 2;
                // aumento la memoria senza tener conto della dimensione della struttura (ottimizzazione)
                dati->linee = realloc(dati->linee, dimc);
            }
        }
    }
    // ridimensiono la memoria al numero di righe effettive
    dati->linee = realloc(dati->linee, dati->n);
}

/* Stampa tutte le righe in ordine inverso */
void stampa_contrario(struct file *dati)
{
    int i, j;
    for (i = dati->n - 1; i >= 0; --i) {
        for (j = NNUM - 1; j >= 0; --j) {
            printf("%d ", dati->linee[i].numeri[j]);
        }
        puts("");
    }
}

/* Calcola e stampa i valori più frequenti tra -100 e 100 */
void max_distribuzione(struct file *dati)
{
    int i, j, num;
    int istogramma[201] = {0};
    int max;

    for (i = 0; i < dati->n; ++i) {
       for (j = 0; j < NNUM; ++j) {
           num = dati->linee[i].numeri[j];
           if ((num >= -100) && (num <= 100)) {
               istogramma[num + 100]++;
           }
       }
    }

    max = istogramma[0];
    for (i = 0; i < 201; ++i) {
        if (istogramma[i] > max)
            max = istogramma[i];
    }

    for (i = 0; i < 201; ++i) {
        if (istogramma[i] == max)
            printf("%d\n", i - 100);
    }
}

/* Conta le righe consecutive che condividono almeno un valore */
int righe(struct file *dati)
{
    int i, j1, j2;
    int trovato, count = 0;

    for (i = 0; i < dati->n - 1; ++i) {
        trovato = 0;
        for (j1 = 0; j1 < NNUM; ++j1) {
            for (j2 = 0; j2 < NNUM; ++j2) {
                if (dati->linee[i].numeri[j1] == dati->linee[i + 1].numeri[j2])
                    trovato = 1;
            }
       }
       count += trovato;
    }
    return count;
}

/* Trova e stampa il valore minimo e massimo tra tutti i numeri */
void stampa_min_max(struct file *dati)
{
    int i, j, num;
    int min = dati->linee[0].numeri[0], max = min;

    for (i = 0; i < dati->n; ++i) {
        for (j = 0; j < NNUM; ++j) {
            num = dati->linee[i].numeri[j];
            if (num > max) max = num;
            if (num < min) min = num;
        }
    }
    printf("%d\n%d\n", min, max);
}

/* Stampa le righe con le rispettive somme */
void stampa_somme(struct file *dati)
{
    int i, j;

    for (i = 0; i < dati->n; ++i) {
        for (j = 0; j < NNUM; ++j) {
            printf("%d ", dati->linee[i].numeri[j]);
        }
        printf("(%d)\n", dati->linee[i].somma);
    }
}

/* Funzione di confronto per l’ordinamento */
int cmp(const void *p1, const void *p2)
{
    const struct linea *a = p1, *b = p2;
    if (a->somma > b->somma) return 1;
    if (a->somma < b->somma) return -1;
    return 0;
}

/* Funzione principale */
int main(int argc, char *argv[])
{
    FILE *f;
    struct file dati;
    
    if (argc != 2) {
        printf("Uso: ./a.out nomefile\n");
        return 1;
    }
    
    if ((f = fopen(argv[1], "r")) == NULL) {
        printf("Errore nell'apertura del file %s\n", argv[1]);
        return 1;
    }

    // leggo i dati dal file
    leggi_file(f, &dati);
    fclose(f);

    puts("[CONTRARIO]");
    stampa_contrario(&dati);
    puts("");
    puts("[DISTRIBUZIONE]");
    max_distribuzione(&dati);
    puts("");
    puts("[NRIGHE]");
    printf("%d\n", righe(&dati));
    puts("[MIN-MAX]");
    stampa_min_max(&dati);
    puts("");
    puts("[ORDINAMENTO]");
    qsort(dati.linee, dati.n, sizeof(*(dati.linee)), cmp);
    stampa_somme(&dati);

    return 0;
}
