/* Soluzione del tema d'esame del 2022-07-28 */

#include <stdio.h>
#include <stdlib.h>

#define NNUM (10) // numero di valori numerici in ogni riga del file

// struttura che rappresenta una riga del file
struct linea {
    int numeri[NNUM]; // array di 10 numeri
    int somma;        // somma dei numeri
};

// struttura che contiene tutte le righe del file
struct file {
    int n;               // numero di righe lette
    struct linea *linee; // puntatore al vettore delle righe
};

/* Funzione che legge il contenuto del file e riempie la struttura dati */
void leggi_file(FILE *f, struct file *dati)
{
    int dimc = 1, s, i;
    struct linea *linea, *tmp;
    char buf[2048];
    
    dati->n = 0;
    // alloco memoria iniziale per una riga; è sufficiente per iniziare
    dati->linee = malloc(dimc * sizeof(*(dati->linee)));

    while (fgets(buf, sizeof(buf), f)) {
        // prendo il puntatore alla riga corrente
        linea = dati->linee + dati->n;

        // leggo i 10 numeri della riga
        sscanf(buf, "%d %d %d %d %d %d %d %d %d %d",
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

        // calcolo la somma dei numeri letti
        s = 0;
        for (i = 0; i < NNUM; ++i) {
            s += linea->numeri[i];
        }
        linea->somma = s;
        dati->n += 1;

        // quando serve, aumento la capacità dell'array
        if (dati->n >= dimc) {
            dimc *= 2;
            tmp = realloc(dati->linee, dimc * sizeof(*(dati->linee)));
            dati->linee = tmp;
        }
    }
    // ridimensiono l’array per adattarlo al numero esatto di righe lette
    dati->linee = realloc(dati->linee, dati->n * sizeof(*(dati->linee)));
}

/* Stampa le righe in ordine inverso */
void stampa_contrario(struct file *dati)
{
    int i, j;
    for (i = dati->n - 1; i >= 0; --i) {
        for (j = NNUM - 1; j >= 0; --j) {
            printf("%d ", dati->linee[i].numeri[j]);
        }
        puts(""); // va a capo dopo ogni riga
    }
}

/* Calcola la distribuzione dei valori e stampa quelli più frequenti */
void max_distribuzione(struct file *dati)
{
    int i, j, num;
    int istogramma[201] = {0}; // per contare i numeri da -100 a +100
    int max;

    // scorro tutte le righe e aggiorno i conteggi
    for (i = 0; i < dati->n; ++i) {
       for (j = 0; j < NNUM; ++j) {
           num = dati->linee[i].numeri[j];
           if ((num >= -100) && (num <= 100)) {
               istogramma[num + 100]++;
           }
       }
    }

    // trovo il massimo valore nell’istogramma
    max = istogramma[0];
    for (i = 0; i < 201; ++i) {
        if (istogramma[i] > max)
            max = istogramma[i];
    }

    // stampo tutti i numeri che hanno la frequenza massima
    for (i = 0; i < 201; ++i) {
        if (istogramma[i] == max)
            printf("%d\n", i - 100);
    }
}

/* Conta quante coppie di righe consecutive hanno almeno un numero in comune */
int righe(struct file *dati)
{
    int i, j1, j2;
    int trovato, count = 0;

    for (i = 0; i < dati->n - 1; ++i) {
        trovato = 0;
        for (j1 = 0; j1 < NNUM; ++j1) {
            for (j2 = 0; j2 < NNUM; ++j2) {
                if (dati->linee[i].numeri[j1] == dati->linee[i + 1].numeri[j2])
                    trovato = 1; // appena ne trovo uno, la condizione è soddisfatta
            }
       }
       count += trovato;
    }
    return count;
}

/* Trova e stampa il valore minimo e massimo tra tutti i numeri letti */
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

/* Stampa le righe con le relative somme */
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

/* Funzione di confronto per ordinare le righe in base alla somma */
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
    
    // apro il file
    f = fopen(argv[1], "r");

    // leggo il file
    leggi_file(f, &dati);
    fclose(f);

    // eseguo tutte le funzioni richieste
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

    // libero la memoria alla fine
    free(dati.linee);
    
    return 0;
}
