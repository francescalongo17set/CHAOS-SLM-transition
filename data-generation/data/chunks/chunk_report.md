# Chunk report (stage 2)

## zurich_salute

- chunks: **164** (estimate 170, difference -4%)
- chars: min 499, median 1577, max 1994; under 300: 0; over 2400: 0
- coverage of extracted text (core, no overlap): 98.9% (dropped sections 1739 chars = 0.8%; kept+dropped = 99.7%)
- forbidden characters: 0
- headings: 122 (0 synthetic, TOC entries not found on page: 0)
- pools: {'train_pool': 132, 'validation_pool': 32}

| top section | pool | chunks | chars |
| --- | --- | ---: | ---: |
| DIP | train_pool | 10 | 11885 |
| DIP aggiuntivo | train_pool | 16 | 19390 |
| Come leggere questo documento | train_pool | 2 | 3442 |
| Glossario | train_pool | 11 | 18788 |
| Sezione 1 - Norme comuni a tutte le garanzie | train_pool | 15 | 20550 |
| Sezione 2 - Protezione Salute | train_pool | 52 | 80341 |
| Sezione 3 - Assistenza | validation_pool | 32 | 47768 |
| Sezione 4 - Tutela Legale | train_pool | 17 | 22456 |
| Allegato 1 - Massimali, limiti di Indennizzo e Scoperto | train_pool | 8 | 11997 |
| Allegato 2 - Adeguamento del Premio per età | train_pool | 1 | 1915 |

**Held-out section** `Sezione 3`: pages 34 to 42, 32 chunks


## generali_immagina_adesso

- chunks: **319** (estimate 320, difference -0%)
- chars: min 414, median 1461, max 2288; under 300: 0; over 2400: 0
- coverage of extracted text (core, no overlap): 99.2% (dropped sections 1297 chars = 0.3%; kept+dropped = 99.5%)
- forbidden characters: 0
- headings: 268 (11 synthetic, TOC entries not found on page: 11)
- pools: {'train_pool': 267, 'validation_pool': 52}

| top section | pool | chunks | chars |
| --- | --- | ---: | ---: |
| DIP | train_pool | 7 | 9969 |
| DIP aggiuntivo | train_pool | 36 | 51155 |
| Presentazione Modulo | train_pool | 12 | 16085 |
| Definizioni | train_pool | 23 | 32511 |
| Prevenzione e assistenza CASA | validation_pool | 52 | 55859 |
| In solidità - Danni ai beni | train_pool | 74 | 108836 |
| In solidità verso gli altri - Danni a terzi | train_pool | 18 | 23484 |
| In guardia - Furto Su misura | train_pool | 14 | 18343 |
| In guardia - Furto Su misura Vip | train_pool | 21 | 31724 |
| In guardia - Furto Tutto compreso | train_pool | 16 | 22319 |
| In guardia - Furto Tutto compreso Vip | train_pool | 22 | 32275 |
| In Guardia: Dedicato a te | train_pool | 11 | 14746 |
| In Guardia: Norme comuni | train_pool | 9 | 15312 |
| Norme Comuni | train_pool | 4 | 5682 |

**Held-out section** `Prevenzione e assistenza CASA`: pages 35 to 53, 52 chunks


## zurich_impresa

- chunks: **536** (estimate 560, difference -4%)
- chars: min 315, median 1608, max 2269; under 300: 0; over 2400: 0
- coverage of extracted text (core, no overlap): 98.9% (dropped sections 3533 chars = 0.5%; kept+dropped = 99.4%)
- forbidden characters: 0
- headings: 296 (0 synthetic, TOC entries not found on page: 0)
- pools: {'test_pool': 536}

| top section | pool | chunks | chars |
| --- | --- | ---: | ---: |
| DIP | test_pool | 12 | 17758 |
| DIP aggiuntivo | test_pool | 183 | 243941 |
| Legenda | test_pool | 2 | 1992 |
| Glossario | test_pool | 18 | 32373 |
| Glossario giuridico valido per la sezione Tutela legale | test_pool | 4 | 6254 |
| Glossario valido per la sezione Assistenza | test_pool | 1 | 398 |
| Norme comuni a tutte le garanzie | test_pool | 16 | 18568 |
| Incendio e Danni ai beni | test_pool | 68 | 111083 |
| Furto | test_pool | 36 | 54858 |
| Danni Indiretti Margine di Contribuzione | test_pool | 18 | 23280 |
| Responsabilità Civile della proprietà del fabbricato | test_pool | 13 | 20593 |
| Responsabilità Civile danni a terzi (R.C.T.) | test_pool | 61 | 96040 |
| Responsabilità Civile danni a terzi da prodotti (R.C.P.) | test_pool | 33 | 50606 |
| Tutela legale | test_pool | 32 | 50562 |
| Assistenza | test_pool | 15 | 24496 |
| Salvareddito | test_pool | 11 | 15865 |
| Allegato 1 - Modelli di denuncia Sinistro | test_pool | 13 | 22265 |

# 20 random chunks per document

## zurich_salute

### zurich_salute_p026_c01 | Sezione 2 - Protezione Salute > Che cosa non è assicurato? | pool=train_pool | 1836 chars
```
Per gli Interventi chirurgici ambulatoriali o effettuati in regime di Day Surgery, la Compagnia corrisponde la diaria giornaliera indicata in Polizza per 1 (uno) solo giorno di Ricovero.
Che cosa non è assicurato?
2.7 Persone non assicurabili
La Compagnia non assicura le persone affette da insulinodipendenza, alcolismo, tossicodipendenza, sieropositività HIV.
Se l’Assicurato è colpito da queste patologie nel corso del contratto:
- l’Assicurazione termina alla prima scadenza annuale dopo la Diagnosi;
- la valutazione concreta dello stato di salute dell’Assicurato non è rilevante;
- l’incasso dei Premi non significa che la garanzia è attiva e tali Premi sono restituiti al Contraente al netto delle imposte.
2.8 Esclusioni valide per tutte le garanzie
Se non diversamente contrattualizzato in Polizza, sono esclusi dall’Assicurazione i Sinistri conseguenti a:
1. Infortuni, Malattie, o stati patologici avvenuti, riscontrati o clinicamente diagnosticati prima della stipula della Polizza. Se l’Assicurato è sottoposto prima della stipula della Polizza ad esami, visite o accertamenti medici sui quali non abbia ancora ricevuto il relativo referto di Diagnosi, se dall’esito di tali accertamenti venissero confermati Infortuni, Malattie o stati patologici, gli stessi verranno considerati pregressi e i relativi Sinistri saranno esclusi dall’Assicurazione;
2. cure e Interventi per l’eliminazione o la correzione di Difetti fisici preesistenti alla stipula della Polizza. Qualora l’Assicurato si sia sottoposto anteriormente alla stipula della Polizza ad esami, visite o accertamenti medici sui quali non abbia ancora ricevuto il relativo referto di Diagnosi, se dall’esito di tali accertamenti venissero confermati Difetti fisici, gli stessi verranno considerati pregressi e i relativi Sinistri saranno esclusi dall’Assicurazione;
```

### zurich_salute_p015_c02 | Sezione 1 - Norme comuni a tutte le garanzie > Quando e come devo pagare? | pool=train_pool | 1144 chars
```
Se il Contraente è una persona fisica e l’Assicurato è un soggetto diverso dal Contraente, l’obbligo descritto in questo articolo è esteso all’Assicurato.
Quando e come devo pagare?
1.7 Pagamento del Premio
Il Premio (o, in caso di pagamento frazionato e di anno più frazione, la prima rata di Premio), deve essere pagato all’Intermediario assicurativo che gestisce la Polizza o alla Compagnia al momento della firma della Polizza; le rate successive devono essere pagate alle scadenze previste, con rilascio di ricevute di pagamento emesse dalla Compagnia o appendici emesse dall’Intermediario assicurativo che indicano la data del pagamento.
Il Premio può essere pagato in un’unica soluzione oppure, a seguito di valutazione da parte della Compagnia, in rate semestrali, quadrimestrali, trimestrali, bimestrali e mensili senza oneri aggiuntivi. Il Premio deve sempre essere pagato per intero in base alla durata della Polizza, anche se è previsto il pagamento in più rate.
Il pagamento può essere effettuato con assegno bancario o circolare, bonifico bancario, carte di debito o credito e denaro contante entro i limiti stabiliti dalla legge.
```

### zurich_salute_p044_c04 | Sezione 4 - Tutela Legale > Che cosa è assicurato e come? > 4.3 Insorgenza del Sinistro – Operatività della garanzia assicurativa | pool=train_pool | 877 chars
```
• dalle ore 24 del giorno di decorrenza della Polizza, a condizione che il Premio sia stato corrisposto, in tutti gli altri casi per determinare la data in cui avviene un Evento, si considera:
a) la data del primo Evento che ha dato origine al diritto al risarcimento, nei casi di richieste di risarcimento per Danni Extracontrattuali
subiti;
b) la data in cui è avvenuta la prima violazione, anche presunta, di una norma di legge o di contratto, da parte dell’Assicurato o della
controparte o di un terzo, nelle ipotesi di controversie contrattuali.
La garanzia si estende agli Eventi manifestatisi entro 2 (due) anni dalla cessazione del contratto, se avvenuti nel Periodo assicurativo.
Se l’Evento si protrae attraverso più violazioni successive della stessa natura, la Compagnia prenderà in considerazione la data in cui si è verificata la prima violazione, anche presunta.
```

### zurich_salute_p037_c02 | Sezione 3 - Assistenza > Che cosa è assicurato e come? > 3.4 Assistenza lontano da casa | pool=validation_pool | 1401 chars
```
Se un Familiare, residente con l’Assicurato come da certificato di stato di famiglia, trovandosi in Viaggio, necessita di rientrare presso la Residenza per ricongiungersi con l’Assicurato, la Struttura Organizzativa metterà a disposizione del Familiare un biglietto aereo (classe economica) o ferroviario (prima classe) di andata e ritorno. La Compagnia terrà a proprio carico il relativo costo. Il Ricongiungimento potrà essere richiesto nei 90 (novanta) giorni successivi alle dimissioni dall’Istituto di cura dell’Assicurato.
20) Accompagnamento di minori
Se l’Assicurato in Viaggio, accompagnato da minori di 15 anni, si trova nell’impossibilità di occuparsi di loro, la Struttura Organizzativa provvederà a fornire un biglietto ferroviario (prima classe) o aereo (classe economica) di andata e ritorno per permettere ad un Familiare, residente nel Territorio Italiano, di raggiungere i minori, prendersene cura e ricondurli alla Residenza. L’Assicurato dovrà comunicare nome, indirizzo e recapito telefonico del Familiare affinché la Struttura Organizzativa possa contattarlo e organizzare il Viaggio. La Compagnia terrà a proprio carico il relativo costo della Prestazione, comprensivo del biglietto ferroviario (prima classe) o aereo (classe economica) del minore senza limiti di Sinistri per Periodo assicurativo. Restano a carico dell’Assicurato le eventuali spese di soggiorno del Familiare.
```

### zurich_salute_p030_c04 | Sezione 2 - Protezione Salute > Cosa fare in caso di Sinistro? > 2.16 Termini di prescrizione | pool=train_pool | 1953 chars
```
Per prenotare e conoscere le strutture convenzionate e specializzate in Esami di routine è necessario invece contattare MyAssistance con le modalità previste ai punti 1. 2. e 3.
2.16 Termini di prescrizione
Ogni diritto derivante dal contratto di Assicurazione si prescrive in 2 (due) anni dal giorno in cui si è verificato l’Evento su cui si fonda il diritto (articolo 2952 del Codice Civile).
Come è gestito il Sinistro?
2.17 Scoperto
2.17.1 Garanzia Spese sanitarie
Fermi i Massimali previsti dalla garanzia o dalla singola prestazione, in caso di Sinistro la Compagnia rimborsa le spese sostenute
ed effettivamente documentate con deduzione per singolo Sinistro della percentuale di Scoperto (con l’applicazione del relativo importo minimo e massimo) se indicata in Polizza, applicata sull’ammontare delle spese sanitarie solo se l’Assicurato si rivolge ad un Istituto di cura e/o professionisti medici non convenzionati con MyAssistance o convenzionati ma senza ricorrere alla forma diretta. Tuttavia, nel caso in cui l’Istituto di cura sia convenzionato con MyAssistance ma il professionista medico che effettua l’Intervento chirurgico non sia convenzionato, il suddetto Scoperto si applica solo all’ammontare delle spese sostenute per il professionista medico, richieste tramite forma indiretta.
Lo Scoperto indicato in Polizza non si applica:
- se l’Assicurato richiede l’attivazione delle prestazioni in copertura attraverso Istituto di cura e /o professionisti medici
convenzionati con MyAssistance, ricorrendo alla forma diretta con le modalità di attivazione della convenzione di cui alla lettera b. "Utilizzo di Istituti di cura o professionisti convenzionati con MyAssistance con pagamento in forma diretta” del punto del punto 2.13;
- alla prestazione prevista alla lettera g. “Indennità sostitutiva per Ricovero a carico del Servizio Sanitario Nazionale” del punto
2.1.2 Ulteriori prestazioni in copertura della garanzia Spese sanitarie;
```

### zurich_salute_p027_c02 | Sezione 2 - Protezione Salute > Che cosa non è assicurato? > 2.8 Esclusioni valide per tutte le garanzie | pool=train_pool | 1246 chars
```
29. Infortuni e Malattie derivanti dallo svolgimento della professione di militare delle Forze Armate o dei Corpi Armati dello Stato, appartenente alle Forze di Polizia, guardia giurata;
30. dolo dell’Assicurato.
Per determinare se un Sinistro è in copertura, si precisa quanto di seguito indicato:
• non si considera Day Hospital la permanenza in un Istituto di cura presso il pronto soccorso;
• in caso di Ricovero non si considera pernottamento, la permanenza notturna in pronto soccorso;
• non si considerano Istituti di cura gli stabilimenti termali, le case di Convalescenza e di soggiorno, nonché i centri benessere e le case di cura aventi finalità dietologiche ed estetiche o deputate alle lungodegenze;
• non si considera la gravidanza una Malattia;
• non si considerano Visite specialistiche le visite effettuate da medici praticanti le Medicine alternative e quelle effettuate dal medico di famiglia, guardia medica e da medici pediatri;
• non si considerano Cure mediche le Visite specialistiche, gli accertamenti diagnostici, gli esami e i medicinali. In aggiunta alle esclusioni riportate al punto 2.8 sono inoltre previste delle specifiche esclusioni suddivise per garanzia così come indicate ai successivi punti 2.9, 2.10 e 2.11.
```

### zurich_salute_p015_c04 | Sezione 1 - Norme comuni a tutte le garanzie > Quando e come devo pagare? > 1.8 Revisione del Premio | pool=train_pool | 1740 chars
```
1.8 Revisione del Premio
a. Adeguamento del Premio per età
In occasione di ogni scadenza annuale della Polizza, la Compagnia adegua, per ciascun Assicurato, il Premio delle garanzie Spese sanitarie, Alta diagnostica e Visite specialistiche applicando i coefficienti per età previsti dall’Allegato 2 “Adeguamento del Premio per età”.
b. Indicizzazione
La Compagnia procede, in occasione di ogni scadenza annuale della Polizza, all’adeguamento dei valori in base alla media ponderata dei pesi relativi agli indici ISTAT 062 “servizi ambulatoriali” e 063 “servizi ospedalieri” (di seguito “indice”). Tali indici
fanno parte dell’indice nazionale dei prezzi al consumo per l’intera collettività (NIC) “Servizi sanitari e spese per la salute” pubblicato dall’ISTAT – Istituto Nazionale di Statistica.
L’indicizzazione si applica a:
- Premi
- Massimali e somme assicurate
- eventuali limiti di Indennizzo se espressi in cifra assoluta. Il calcolo della variazione è effettuato nel seguente modo:
- alla Polizza è assegnato come riferimento iniziale l’indice del mese di giugno dell’anno solare antecedente a quello della sua data
di effetto;
- alla scadenza di ogni rata annuale della Polizza si considera l’indice del mese di giugno dell’anno solare precedente a quello della
scadenza;
- si effettua il confronto tra i due indici e si quantifica la relativa variazione;
- se è positiva si avrà una variazione in aumento, se negativa in diminuzione, se non c’è differenza non ci sarà alcuna variazione.
L’adeguamento automatico si applica alla somma totale dei Premi delle garanzie soggette all’adeguamento per l’età (come previsto alla lettera a. Adeguamento del Premio per età) e dei Premi relativi alle restanti garanzie richiamate in Polizza.
```

### zurich_salute_p044_c03 | Sezione 4 - Tutela Legale > Che cosa è assicurato e come? > 4.2 Persone assicurate | pool=train_pool | 1881 chars
```
- tutte le persone assicurate abbiano acquistato la garanzia Spese Legali. Ad esempio, per poter estendere gratuitamente la
garanzia “Spese legali” ai bambini con età inferiore ad otto anni, oltre ai genitori anche eventuali altri fratelli o sorelle già indicati in Polizza devono aver acquistato la garanzia ‘Spese legali’ altrimenti il figlio minore di 8 anni beneficia della sola garanzia Consulenza legale telefonica
L’estensione è prestata fino al minore tra i Massimali della garanzia Spese legali previsti per tutte le persone assicurate.
Per il rinnovo successivo al periodo di gratuità, il Premio sarà comunicato dalla Compagnia sulla base della tariffa vigente.
4.3 Insorgenza del Sinistro – Operatività della garanzia assicurativa
In riferimento alla garanzia Consulenza legale telefonica
Un Evento è considerato in garanzia se avviene dalle ore 24 del giorno di decorrenza della Polizza. Il Sinistro avviene nel momento in cui l’Assicurato, la controparte o un terzo inizia a violare norme di legge o di contratto.
Per determinare la data in cui avviene un Evento, si considera:
a) la data del primo Evento che ha dato origine al diritto al risarcimento, nei casi di richieste di risarcimento per Danni Extracontrattuali
subiti;
b) la data in cui è avvenuta la prima violazione, anche presunta, di una norma di legge o di contratto, da parte dell’Assicurato o della
controparte o di un terzo, nelle ipotesi di controversie contrattuali.
In riferimento alla garanzia Spese Legali
Un Evento è considerato in garanzia se avviene:
• trascorsi 90 giorni dalla data di decorrenza della Polizza, a condizione che il Premio sia stato corrisposto, in caso di controversie contrattuali;
• dalle ore 24 del giorno di decorrenza della Polizza, a condizione che il Premio sia stato corrisposto, in tutti gli altri casi per determinare la data in cui avviene un Evento, si considera:
```

### zurich_salute_p027_c04 | Sezione 2 - Protezione Salute > Che cosa non è assicurato? > 2.11 Esclusioni valide per la garanzia Diaria da Ricovero | pool=train_pool | 1661 chars
```
2.11 Esclusioni valide per la garanzia Diaria da Ricovero
L’Assicurazione non è operante:
- in assenza di prescrizione medica per la prestazione “Diaria da Convalescenza”;
- in caso di (i) cura dell’ittero neonatale; (ii) Ricoveri del neonato in assenza di patologia accertata, per la prestazione “Copertura
per figli neonati”.
2.12 Periodi di Carenza – inoperatività della garanzia
Non sono in copertura:
1. le Malattie che si Manifestano nei trenta (30) giorni successivi a quello di effetto della Polizza o all’inserimento di una nuova persona assicurata, anche se diagnosticate successivamente. Per le Malattie dipendenti da gravidanza o puerperio la garanzia è operante a condizione che la stessa abbia avuto inizio dopo la data di effetto della Polizza;
2. nei trenta (30) giorni successivi a quello di effetto della Polizza o all’inserimento di una nuova persona assicurata,
- l’aborto spontaneo o terapeutico;
- l’aborto conseguente a traumatologia del feto a seguito di atto violento nei confronti dell’Assicurata;
- l’aborto conseguente a traumatologia del feto a seguito di Eventi accidentali occorsi all’Assicurata, quali ad esempio
incidente stradale e cadute;
- l’interruzione volontaria di gravidanza avvenuta a seguito di violenza sessuale nei confronti dell’Assicurata a condizione che
la gravidanza abbia avuto inizio dopo la data di effetto della Polizza;
3. nei trecento (300) giorni successivi a quello di effetto della Polizza, o all’inserimento di una nuova persona assicurata il parto e le patologie varicose;
4. nei centottanta (180) giorni successivi a quello di effetto della Polizza o all’inserimento di una nuova persona assicurata,
```

### zurich_salute_p020_c02 | Sezione 2 - Protezione Salute > Che cosa è assicurato e come? > 2.1 Garanzia Spese sanitarie | pool=train_pool | 1905 chars
```
- i bambini di età inferiore ad otto anni sono espressamente indicati in Polizza tra le persone assicurate insieme ad entrambi
i genitori o affidatari risultanti dallo stato di famiglia. Nei casi di decesso di un genitore, separazione legale, divorzio o non riconoscimento del figlio da parte di un genitore, l’estensione gratuita è prevista anche in presenza di Nucleo familiare composto da un solo genitore espressamente indicato in Polizza e risultante dallo stato di famiglia;
- tutti gli Assicurati indicati in Polizza hanno acquistato la garanzia oggetto di estensione gratuita (ad esempio, per poter
estendere gratuitamente la garanzia “Spese sanitarie” ai bambini con età inferiore a otto anni, anche eventuali altri fratelli o sorelle già indicati in Polizza devono aver acquistato la medesima garanzia).
L’estensione è prestata per la forma di garanzia con Scoperto più elevato, tra tutte le forme di garanzia acquistate dalle persone assicurate indicate in Polizza.
Per il rinnovo successivo al periodo di gratuità, il Premio sarà comunicato dalla Compagnia sulla base della tariffa vigente.
d. Infortunio in assenza di Ricovero
In caso di Infortunio che non abbia comportato il Ricovero presso un Istituto di cura, la Compagnia rimborsa entro il limite del Massimale indicato nell’Allegato 1 “Massimali, limiti di Indennizzo e Scoperto”, le spese sanitarie sostenute:
- in sede di primo soccorso prestato nell’immediatezza dell’Infortunio in strutture specializzate (come, ad esempio, il Pronto
soccorso ospedaliero o un centro traumatologico territoriale) per assistenza medica, medicinali somministrati, applicazione di apparecchi gessati, accertamenti diagnostici e trasporto dell’Assicurato in ambulanza;
- entro 6 mesi dalla data dell’Infortunio per Cure mediche, gessatura, Trattamenti fisioterapici e rieducativi, acquisto di apparecchi
protesici ortopedici e di tutori preconfezionati.
```

### zurich_salute_p041_c02 | Sezione 3 - Assistenza > Che cosa non è assicurato? > 3.10 Esclusioni | pool=validation_pool | 1751 chars
```
Infortuni ed intossicazioni dovuti ad alcolismo e abuso di psicofarmaci, uso non terapeutico di stupefacenti, allucinogeni e simili, nonché quelli avvenuti alla guida di veicoli e natanti, quando all’Assicurato sia contestato il reato di guida in stato di ebbrezza con tasso alcolemico accertato superiore a 1,2 g/l, oppure senza indicazione specifica del tasso alcolemico rilevato in quanto l’Assicurato si è rifiutato di sottoporsi al relativo test;
k) Malattie e Infortuni cronici e/o preesistenti, ovvero le patologie e le condizioni mediche a esse correlate oggettivamente
constatabili i cui sintomi si siano manifestati nei 5 (cinque) anni precedenti la data di inizio della copertura, di cui l’Assicurato o i suoi familiari avrebbero dovuto presumibilmente essere a conoscenza, a prescindere dal fatto di essere state o meno diagnosticate o curate.
La copertura non opera inoltre in caso di:
• dimissioni volontarie dell’Assicurato contro il parere dei sanitari dell’Istituto di cura presso il quale si trova ricoverato;
• rinuncia o ritardo da parte dell’Assicurato nell’accettare le Prestazioni proposte dalla Struttura Organizzativa;
• circostanze eccezionali di entità e gravità tale da richiedere misure restrittive da parte delle autorità competenti (nazionali e/o internazionali) al fine di ridurre il rischio alla popolazione civile. A solo titolo esemplificativo e non limitativo: chiusura di scuole e aree pubbliche, limitazione di trasporti pubblici in città, limitazione al trasporto aereo. Pertanto tutte le Prestazioni erogate per tramite della Struttura Organizzativa saranno compiute in conformità e nei limiti fissati dalle leggi e/o dalle disposizioni amministrative nazionali ed internazionali, salvo cause di forza maggiore.
```

### zurich_salute_p043_c02 | Sezione 4 - Tutela Legale > Che cosa è assicurato e come? | pool=train_pool | 1765 chars
```
La sostituzione del fornitore avverrà senza modifiche in peggioramento delle condizioni contrattuali e di Premio pattuite con il Contraente.
Che cosa è assicurato e come?
4.1 Oggetto dell’Assicurazione
La sezione Tutela Legale si compone di due garanzie specifiche: Consulenza legale telefonica e Spese Legali.
Consulenza Legale Telefonica
La garanzia è sempre operante per tutti gli Assicurati indicati in Polizza. La Compagnia offre l’accesso, tramite DAS, a un servizio assicurativo di consulenza legale telefonica erogato da consulenti legali esperti, allo scopo di:
· affrontare in modo corretto controversie di natura legale;
· impostare correttamente comunicazioni rivolte a controparti, come ad esempio richieste di risarcimento o diffide;
· ottenere chiarimenti su leggi, decreti e normative vigenti.
La Consulenza legale telefonica opera nel caso in cui il Contraente e l’Assicurato, nell’ambito della propria vita privata extraprofessionale siano rimasti vittime di Infortunio o Malattia indennizzabile secondo quanto disciplinato dalla Sezione 2 - Protezione Salute:
a) per sostenere controversie nei confronti di ospedali, case di cura o medici per danni subiti dovuti a negligenza o inadeguatezza
dell’attività professionale ad esso prestata in qualità di paziente;
b) per sostenere richieste di risarcimento danni alla persona o a cose di sua proprietà, dovuti a Fatto illecito di terzi;
c) per sostenere controversie di natura contrattuale relative all’acquisto di beni e di servizi, in relazione all’ambito salute;
d) per difendersi in un procedimento penale correlato all’Infortunio indennizzabile a termini di Polizza. Il servizio fornisce inoltre informazioni specifiche in merito alla normativa sulla protezione dei Dati personali.
Spese Legali
```

### zurich_salute_p032_c05 | Sezione 2 - Protezione Salute > Come è gestito il Sinistro? > 2.20 Procedura per la valutazione del danno | pool=train_pool | 1417 chars
```
2.20 Procedura per la valutazione del danno
Le conseguenze invalidanti del Sinistro sono concordate con le seguenti modalità:
a) direttamente dalla Compagnia o persona da questa incaricata, con l’Assicurato o persona da lui designata; oppure
b) su richiesta di una delle Parti, tra due Medici nominati rispettivamente uno dalla Compagnia e uno dall’Assicurato, con apposito
atto unico.
Ciascun Medico ha facoltà di farsi assistere e affiancare da altri Medici specialisti, che potranno intervenire nelle operazioni peritali senza avere alcun potere decisionale. In caso di inattività di una delle Parti quella più diligente, decorsi 20 giorni dalla comunicazione di richiesta di nomina, farà istanza al Consiglio dell’Ordine dei Medici, avente giurisdizione nel luogo ove deve riunirsi il Collegio dei Medici per la nomina del Medico di parte. Il Collegio medico risiede nella città dove ha sede l’Istituto di Medicina Legale più vicina al luogo di residenza o domicilio dell’Assicurato.
In caso di disaccordo sulle conseguenze invalidanti del Sinistro o su richiesta di uno dei Medici:
1. entro 30 giorni dalla relativa verbalizzazione i due Medici devono nominarne un terzo scelto tra una terna di nominativi proponibile da entrambe le parti;
2. qualora non ci sia accordo verbalizzato su alcuno dei nominativi proposti, la parte più diligente proporrà, entro 30 giorni dalla data di detto verbale altri nominativi;
```

### zurich_salute_p012_c01 | Glossario | pool=train_pool | 1652 chars
```
Malformazione - deviazione dal normale assetto morfologico di un organismo o di parti di suoi organi per condizioni morbose congenite.
Malware - Qualsiasi Software o codice dannoso (come ad esempio virus, spyware, worm, trojan, rootkit, ransomware, keylogger, dialer e rogue security Software o qualsiasi altro strumento equiparabile) progettato per ottenere l’accesso illecito, cancellare o corrompere Dati elettronici, danneggiare o disgregare una qualsiasi rete o Sistema informativo, eludere qualunque prodotto o servizio di sicurezza e/o interrompere il funzionamento del sistema informatico.
Medicina alternativa o complementare - Le pratiche mediche “non convenzionali” definite dalla Federazione Nazionale degli Ordini dei Medici e degli Odontoiatri (agopuntura, fitoterapia, medicina ayurvedica, medicina antroposofica, medicina omeopatica, medicina tradizionale cinese, omotossicologia e chiropratica).
Manifestazione (di Malattia) - il presentarsi di uno o più segni o sintomi riconducibili alla Malattia.
Massimale - La somma massima rimborsabile fino al raggiungimento della quale, per ciascun Assicurato e per Periodo assicurativo, la Compagnia presta la garanzia.
Network / Rete - La Rete convenzionata della Società MyAssistance S.r.l., costituita da Istituti di cura, centri diagnostici e poliambulatori, nonché da professionisti medici che provvedono all’erogazione delle prestazioni. L’elenco delle strutture sanitarie convenzionate è direttamente consultabile sul sito http://www.myassistance.it/networks/network-medicale/elenco-strutture.html oppure attraverso il link presente sul sito istituzionale della Compagnia www.zurich.it.
```

### zurich_salute_p029_c03 | Sezione 2 - Protezione Salute > Cosa fare in caso di Sinistro? | pool=train_pool | 1760 chars
```
- rimborso per le spese a lui intestate, documentate ed indennizzabili previste dai punti 2.1.1 e 2.1.2 per la garanzia Spese sanitarie,
2.2.1e 2.2.2 per la garanzia Alta Diagnostica, 2.3.1 e 2.3.2 per la garanzia Visite specialistiche;
- erogazione, qualora indennizzabile, dell’indennità sostitutiva per Ricovero prevista al punto 2.1.2 lettera g), della diaria da
Convalescenza prevista ai punti 2.1.2 lettera k) e punto 2.6.2 lettera d) e della Diaria da Ricovero prevista al punto 2.6.1 nei casi di seguito elencati:
- prestazione erogata da Istituti di cura e/o professionisti non convenzionati con MyAssistance;
- prestazione erogata da Istituti di cura e/o professionisti convenzionati con MyAssistance senza richiesta del pagamento diretto
così come indicato alla lettera b. “Utilizzo di Istituti di cura e/o professionisti convenzionati MyAssistance con pagamento in forma diretta”;
- ogni altra qualsivoglia spesa non riconducibile a Istituti di cura e/o professionisti medici.
Il Contraente, l’Assicurato o i suoi aventi diritto devono denunciare il Sinistro entro 3 (tre) giorni da quando ne hanno avuto conoscenza, o comunque appena ne abbiano la possibilità. La denuncia di Sinistro deve essere fatta tramite il proprio Intermediario assicurativo oppure tramite app Zurich One, così come indicato al precedente punto a) Modalità di denuncia di Sinistro e deve essere accompagnata dalla seguente documentazione medica e di spesa, intestata all’Assicurato:
- copie di fatture in caso di esami, Visite specialistiche ed accertamenti diagnostici previsti dalle garanzie “Spese sanitarie”. “Visite
specialistiche” e “Alta Diagnostica”;
- copie di cartella clinica completa e Scheda di Dimissione Ospedaliera (O.S.D.) in caso di Ricovero, Day Surgery;
```

### zurich_salute_p046_c04 | Sezione 4 - Tutela Legale > Cosa fare in caso di Sinistro? > 4.9 Fasi di gestione del Sinistro e scelta legale | pool=train_pool | 1088 chars
```
b) se l’Assicurato non fornisce tale indicazione, DAS può individuare direttamente il legale;
c) l’Assicurato deve conferire in ogni caso regolare mandato al legale individuato fornendo allo stesso tutte le informazioni e la
documentazione necessarie per consentire la miglior tutela dei propri interessi;
d) qualora nel corso dello stesso grado di giudizio l’Assicurato decida di revocare l’incarico professionale conferito a un legale e di
dare incarico a un nuovo legale, DAS non rimborserà le spese del nuovo legale riferite ad attività già svolte dal primo avvocato. Tale disposizione non si applica nel caso di rinuncia all’incarico da parte del legale.
DAS gestirà a tutti gli effetti un unico Sinistro:
a) in presenza di vertenze, promosse da o contro una o più persone e aventi per oggetto domande identiche o connesse;
b) in presenza di procedimenti, anche di natura diversa, dovuti al medesimo Evento-fatto nei quali siano coinvolti uno o più Assicurati;
c) qualora l’Evento che dà diritto alle prestazioni si protragga attraverso più violazioni successive della stessa natura.
```

### zurich_salute_p035_c05 | Sezione 3 - Assistenza > Che cosa è assicurato e come? > 3.3 Cure e protezione | pool=validation_pool | 1564 chars
```
• il ritiro della relativa indicazione medica scritta presso la Residenza o il Domicilio dell’Assicurato e del denaro necessario all’acquisto dei medicinali e/o degli articoli sanitari;
• l’acquisto e la consegna a Domicilio di quanto indicato dal medico curante.
La consegna dei farmaci a domicilio può essere richiesta tutti i giorni 24 ore su 24; Il servizio è fornito dalle ore 9:00 alle 18:00. Sono esclusi dalla consegna i farmaci in classe A, ritenuti essenziali (salvavita) e classe H che per caratteristiche farmacologiche, o per innovatività o per altri motivi di sicurezza, non possono essere utilizzati al di fuori degli Istituti di cura.
La Compagnia tiene a proprio carico il costo del ritiro di quanto indicato dal medico curante e della consegna dei farmaci e/o degli articoli sanitari, con il limite di 3 (tre) Sinistri per Periodo assicurativo e 2 (due) Prestazioni per Sinistro. Sono a carico dell’Assicurato i costi relativi ai medicinali e/o articoli sanitari. Per questa prestazione la Struttura Organizzativa definirà preventivamente le modalità di erogazione del servizio; a tal fine, la Prestazione dovrà essere attivata con almeno 48 ore di anticipo per consentire alla Struttura Organizzativa di disporre il servizio stesso.
8) Care Management
Se l’Assicurato, a seguito di terapia medico/farmacologica, necessita di un periodo di Convalescenza presso la Residenza o il Domicilio, la Struttura Organizzativa, su semplice richiesta telefonica dell’Assicurato provvede all’invio di:
• operatore sanitario/infermieristico;
• fisioterapista;
```

### zurich_salute_p032_c04 | Sezione 2 - Protezione Salute > Come è gestito il Sinistro? > 2.19 Pagamento dell’Indennizzo | pool=train_pool | 747 chars
```
Il pagamento dell’Indennizzo viene effettuato, a cura ultimata, in Italia e in Euro, anche per le spese sostenute all’estero, in valuta diversa dall’Euro, al tasso di cambio rilevato dalla Banca Centrale Europea il giorno in cui sono state sostenute le spese.
Ai fini della denuncia l’Assicurato può fornire la documentazione medica e fiscale (come ad esempio parcelle, onorari, fatture, cartelle cliniche) in fotocopia o scannerizzata. La Compagnia si riserva la facoltà (sia per il pagamento in forma diretta sia indiretta) di richiedere la documentazione in originale per eventuali approfondimenti che dovrà essere consegnata all’Intermediario assicurativo. Gli originali verranno restituiti all’Assicurato tramite l’Intermediario assicurativo.
```

### zurich_salute_p020_c01 | Sezione 2 - Protezione Salute > Che cosa è assicurato e come? > 2.1 Garanzia Spese sanitarie | pool=train_pool | 1611 chars
```
- interruzione volontaria di gravidanza solo se avvenuta a seguito di violenza sessuale nei confronti dell’Assicurata e accertata
da referto medico e denuncia presentata alle Autorità competenti.
b. Copertura per figli neonati
La Compagnia estende gratuitamente ai figli neonati l’Assicurazione della madre, fino alla successiva scadenza e comunque non oltre 180 giorni dalla nascita, per le medesime garanzie e per il medesimo Massimale e Scoperto previsti per la madre al momento della loro nascita. Sono, inoltre, comprese anche le spese sanitarie relative ai Ricoveri per interventi di correzione o eliminazione di Malformazioni congenite e relativi Interventi di chirurgia plastica ricostruttiva, anche a scopo estetico. L’estensione gratuita sarà operativa a condizione che la nascita avvenga dopo il 300esimo giorno successivo a quello di effetto dell’Assicurazione della madre e, in tal caso, la copertura verrà prestata senza i Termini di Carenza. Decorso il termine dei 180 giorni la presente garanzia cessa il suo effetto.
c. Copertura per figli e minori in affidamento preadottivo di età inferiore ad otto anni Se il Contraente ne fa richiesta e dopo valutazione del Questionario anamnestico da parte della Compagnia, la garanzia per le sole spese previste al punto 2.1.1 è operante gratuitamente per i figli e i minori in affidamento preadottivo fino alla prima scadenza annua successiva al compimento dell’ottavo anno di età.
Tale estensione è prestata a condizione che:
- i bambini di età inferiore ad otto anni sono espressamente indicati in Polizza tra le persone assicurate insieme ad entrambi
```

### zurich_salute_p039_c02 | Sezione 3 - Assistenza > Che cosa è assicurato e come? > 3.5 Assistenza durante e post Ricovero, Day Hospital, Day Surgery | pool=validation_pool | 1234 chars
```
Restano a carico dell’Assicurato le spese relative al carburante e ad eventuali pedaggi (autostrade, traghetti, etc.).
33) Video consulto per secondo parere medico rispetto a terapia in corso Se l’Assicurato desidera un secondo parere medico sulle terapie proposte, la Struttura Organizzativa metterà a disposizione dell’Assicurato una consulenza video con il proprio medico di struttura, che potrà eventualmente coordinare, qualora se ne ravvisino i presupposti, un servizio di second opinion con uno specialista del settore. Il collegamento video avviene tramite piattaforma web tra l’Assicurato e il medico specialista affinché quest’ultimo possa fornire un parere su risultati di esami effettuati, terapie prescritte o seguite, approfondimenti rispetto ad un’opinione medica precedentemente ricevuta. Il medico fornisce confronto solo per i casi in cui non è necessario un contatto fisico. Si precisa che tali video consulti medici, considerate le modalità di prestazione del servizio, non costituiscono Diagnosi e sono prestati sulla base delle informazioni e dichiarazioni fornite a distanza dall’Assicurato. La Prestazione potrà essere richiesta tutti i giorni 24 ore su 24; il servizio verrà fornito dalle ore 9:00 alle 18:00.
```

## generali_immagina_adesso

### generali_immagina_adesso_p120_c01 | In guardia - Furto Tutto compreso Vip > Che cosa è assicurato? > Cose assicurate > Mezzi di protezione e chiusura per appartamento non su piano intermedio | pool=train_pool | 1751 chars
```
- ferro a piena sezione dello spessore minimo di 15 mm, ancorate nel muro, con luci, se rettangolari, con lati di misura rispettivamente non maggiore di 50 e 18 cm oppure, se non rettangolari, di forma inscrivibile nei predetti rettangoli o di superficie non maggiore di 400 cm2. B) IMPIANTO DI ALLARME
I locali che contengono le cose assicurate siti nell’ubicazione indicata nella specifica sezione di Polizza devono essere dotati di o presidiati da:
-
Impianto di allarme antintrusione collegato a centrale di telesorveglianza almeno con linea telefonica commutata tramite combinatore telefonico digitale, se la somma assicurata alla Partita Contenuto Denaro e Valori-Documenti non è superiore a 100.000,00 euro oppure
-
Impianto di allarme antintrusione collegato a centrale di telesorveglianza con ponte radio bidirezionale e l’Impianto deve essere attivato.
La Garanzia opera anche quando:
1. il Furto è commesso attraverso aperture protette da mezzi di protezione e chiusura che non rispondono alle caratteristiche di cui sopra;
2. il Furto è commesso con rimozione di Porte blindate, di inferriate, di Serramenti o di serrature applicate agli stessi, senza rottura o forzatura delle relative strutture o sedi di installazione;
3. il Furto è commesso rimuovendo dalla propria sede, con effrazione del telaio, lastre di vetro stratificato di sicurezza;
4. l’Impianto di allarme non è stato attivato.
Ci sono limiti di copertura
•
Se si verifica una sola delle ipotesi sopraindicate, la Garanzia opera con applicazione di uno Scoperto del 25%.
•
Se si verificano l’ultima ipotesi sopraindicata e una delle tre precedenti, la Garanzia opera con applicazione di uno Scoperto del 35%.
•
In ogni caso, il limite massimo di Indennizzo è 50.000,00 euro.
```

### generali_immagina_adesso_p044_c03 | Prevenzione e assistenza CASA > Casa Plus > Che cosa NON è assicurato? | pool=validation_pool | 716 chars
```
Che cosa NON è assicurato?
Art. 2.1 Esclusioni
Le Prestazioni non sono previste per gli eventi accaduti:
a) in occasione di terremoti, eruzioni vulcaniche, alluvioni, maremoti e in occasione di tutti quei fenomeni
atmosferici con caratteristiche di calamità naturali;
b) in occasione di atti di guerra, atti di terrorismo, invasione, occupazione militare, insurrezione, tumulto popolare,
scioperi, sommosse;
c) in occasione di esplosioni o di emanazione di calore o di radiazioni provenienti da trasmutazioni del nucleo
dell’atomo, o in occasione di radiazioni provocate dall’accelerazione artificiale di particelle atomiche;
d) per dolo dell’Assicurato;
ASSISTENZA CASA PLUS
e) per intervento di Pubbliche Autorità.
```

### generali_immagina_adesso_p035_c01 | Prevenzione e assistenza CASA | pool=validation_pool | 806 chars
```
CONDIZIONI SPECIFICHE Prevenzione e Assistenza CASA
PREMESSA
Generali Italia ha stipulato specifica convenzione con EUROP ASSISTANCE ITALIA S.p.A., con sede in Assago (MI) Via del Mulino, 4 - Indirizzo di posta elettronica certificata (PEC) EuropAssistanceItaliaSpA@pec.europassistance.it, in base alla quale la stessa provvede, per conto di Generali Italia e tramite la propria Struttura Organizzativa, al contatto con l’Assicurato e all’organizzazione e fornitura delle Prestazioni di cui alla presente sezione entro i diversi limiti nella stessa previsti e con costi a carico di Generali Italia. Per attivare le Prestazioni previste dalla presente sezione, la Struttura Organizzativa di Europ Assistance Italia S.p.A. può essere contattata ai seguenti numeri: 800 880 880 - dall’estero +39 02 8295 1155.
```

### generali_immagina_adesso_p036_c02 | Prevenzione e assistenza CASA > Casa Start > Che cosa è assicurato? > Invio di un vetraio per interventi di emergenza | pool=validation_pool | 1304 chars
```
Art. 1.5 Invio di un vetraio per interventi di emergenza
Che cosa è assicurato
In caso di Incendio, Esplosione, Scoppio, fulmine, Allagamento, atti vandalici, Furto o tentato Furto, che provocano la rottura dei vetri esterni dell’Abitazione, la cui sicurezza non è più garantita, la Struttura Organizzativa invia all’Assicurato un vetraio.
Ci sono limiti di copertura
I costi di uscita e di manodopera sono a carico della Struttura Organizzativa fino a un massimo di 300,00 euro per Sinistro. I costi dei materiali necessari alla riparazione restano a carico dell’Assicurato.
Art. 1.6 Trasferimento di mobili
Che cosa è assicurato
Quando in caso di Incendio, Esplosione, Scoppio, fulmine, Allagamento, atti vandalici, Furto o tentato Furto, è necessario il trasferimento degli oggetti dall’Abitazione ad altro luogo, la Struttura Organizzativa, in base alle disponibilità locali, mette a disposizione dell’Assicurato un veicolo che può essere guidato con patente B.
La Prestazione opera dal lunedì al venerdì dalle ore 09:00 alle ore 18:00, esclusi i giorni festivi infrasettimanali.
Ci sono limiti di copertura
I costi del noleggio (nel rispetto delle condizioni richieste dal noleggiatore) sono a carico della Struttura Organizzativa fino a un massimo di 300,00 euro per Sinistro.
ASSISTENZA CASA START
```

### generali_immagina_adesso_p056_c01 | In solidità - Danni ai beni > Casa Start > Rischi Assicurati | pool=train_pool | 1878 chars
```
rottura accidentale di lampadari, compresi i danni agli stessi, appesi o fissati ai soffitti e ai muri, a seguito di loro caduta,
se assicurata la Partita Contenuto.
Ci sono limiti di copertura
Se nella specifica sezione di Polizza è indicato Abitazione in corso di costruzione o ristrutturazione, Generali Italia indennizza solo i danni materiali e diretti causati all’Immobile dagli eventi di cui alle precedenti lettere da a. a h.
Art. 2.2 Spese supplementari
Che cosa è assicurato
In caso di Sinistro indennizzabile in base alle Garanzie attivate, Generali Italia rimborsa, fino alla somma indicata nella specifica sezione di Polizza, le spese supplementari sostenute per:
a. demolizione e sgombero: demolire, sgomberare, trasportare, trattare e smaltire i residui del Sinistro al più vicino scarico
o a quello imposto dall’autorità,
b. ricollocamento Contenuto: rimuovere, depositare e ricollocare il Contenuto quando è necessario per ripristinare i locali
danneggiati occupati dal Contraente, se assicurata la Partita Contenuto;
c. alloggio temporaneo: l’alloggio, per il tempo necessario a ripristinare i locali danneggiati occupati dall’Assicurato e
diventati inabitabili a seguito di Sinistro.
Che cosa NON è assicurato
Nessun Indennizzo spetta all’Assicurato per ritardi nel ripristino dei locali danneggiati dovuti a cause eccezionali o per qualsiasi ritardo di occupazione dei locali ripristinati. Ci sono limiti di copertura
La copertura opera col limite di Indennizzo di 150,00 euro al giorno per massimo 100 giorni.
d. onorario dei periti: l’onorario del perito scelto e nominato dal Contraente per la procedura della valutazione del danno e
la quota parte di spese e onorari a suo carico a seguito della nomina del terzo perito.
Ci sono limiti di copertura
La copertura opera fino al 5% dell’ammontare del Sinistro liquidato, col limite massimo di 1.500,00 euro.
```

### generali_immagina_adesso_p012_c01 | DIP aggiuntivo > REGIME FISCALE | pool=train_pool | 1614 chars
```
MODULO CASA - IN SOLIDITÀ | PAG.
CONDIZIONI SPECIFICHE IN SOLIDITÀ - DANNI AI BENI | 36
Che cosa è assicurato? | 36
Art. 1.1 Cose assicurate | 36
Art. 1.2 Condizioni di assicurabilità | 36
Art. 1.2.1 Caratteristiche delle abitazioni | 36
Art. 1.2.2 Abitazione in legno | 37
Art. 1.2.3 Abitazione in corso di costruzione o ristrutturazione | 37
Art. 2.1 Rischi Assicurati | 37
Art. 2.2 Spese supplementari | 38
Art. 2.3 Spese per modifiche costruttive al fabbricato | 38
Art. 2.4 Trasloco | 39
Art. 2.5 Abitazione assicurata anche con polizza fabbricati civili di Generali Italia | 39
Che cosa è assicurato? Garanzie accessorie | 39
Art. 2.6 Danni ai beni altrui | 39
Art. 2.6.1 Ricorso terzi | 39
Art. 2.6.2 Rischio locativo | 40
Che cosa è assicurato? Garanzie accessorie | 40
EVENTI STRAORDINARI | 40
Art. 2.7 Eventi sociopolitici | 40
Art. 2.8 Guasti causati dai ladri e furto di fissi e infissi | 41
EVENTI NATURALI | 41
Art. 2.9 Operatività delle garanzie - Termine di aspettativa | 41
Art. 2.10 Facoltà di recesso | 42
EVENTI ATMOSFERICI | 42
Art. 2.11 Eventi atmosferici | 42
Art. 2.12 Grandine su fragili | 42
Art. 2.13 Eventi atmosferici su impianti a energia rinnovabile | 43
Art. 2.14 Estensione alle tende frangisole dotate di anemometro | 42
Art. 2.15 Sovraccarico di neve | 43
EVENTI CATASTROFALI | 44
Art. 2.16 Terremoto | 44
Art. 2.16.1 Caratteristiche costruttive del fabbricato | 45
Art. 2.17 Alluvione, Inondazione | 45
Art. 2.18 Allagamento e Bombe d'acqua | 45
IMPIANTI | 46
IMPIANTO ELETTRICO | 46
Art. 2.19 Fenomeni elettrici | 46
IMPIANTO IDRICO E TERMICO | 47
Art. 2.20 Acqua condotta | 47
```

### generali_immagina_adesso_p014_c02 | DIP aggiuntivo > REGIME FISCALE | pool=train_pool | 414 chars
```
Dove vale la copertura? | 64
Art. 2.1.4 Danni da spargimento d'acqua per occlusione delle tubazioni e rigurgito fognature | 70
Art. 2.1.5 Danni da inquinamento accidentale | 70
Che cosa è assicurato? Garanzie accessorie | 70
Art. 2.2 Responsabilità civile della conduzione dell’immobile | 70
Art. 2.3 Responsabilità civile della propietà dei terreni non pertinenziali | 71
DEDICATO A TE | 71
CASA INVESTIMENTO | 71
```

### generali_immagina_adesso_p065_c01 | In solidità - Danni ai beni > Che cosa è assicurato? Garanzie accessorie > Impianto elettrico > Fenomeni elettrici | pool=train_pool | 657 chars
```
• per i danni subiti dall’Impianto solare termico o dall’Impianto fotovoltaico, se questi sono dotati di dichiarazioni di conformità agli standard IEC61730 e IEC62109 e se l’Assicurato ha effettuato la manutenzione ordinaria in base alle disposizioni del fornitore o della ditta installatrice. Le riduzioni di Franchigia indicate non sono cumulabili tra loro.
IMPIANTO IDRICO E TERMICO
Le altre Garanzie Impianto idrico e termico possono essere attivate se attivata la Garanzia Acqua condotta. Per attivare la Garanzia Spese di ricerca e riparazione fuoriuscita gas è necessario aver attivato anche la Garanzia Spese di ricerca e riparazione acqua condotta.
```

### generali_immagina_adesso_p105_c01 | In guardia - Furto Su misura Vip > Che cosa è assicurato? > Cose assicurate > Mezzi di protezione e chiusura per villa isolata | pool=train_pool | 1655 chars
```
Art. 1.2.4 Mezzi di protezione e chiusura per villa isolata
Mezzi di chiusura e di protezione dei locali
Che cosa è assicurato
LOCALI INCUSTODITI
Per l’indennizzabilità dei danni avvenuti nei locali, a eccezione di quelli da Rapina, quando gli stessi restano incustoditi, devono essere presenti le seguenti condizioni:
A) APERTURE VERSO L’ESTERNO
-
Ogni ingresso dei locali che contengono le cose assicurate nell’ubicazione indicata nella specifica sezione di
Polizza deve essere difeso da Porta blindata chiusa con serratura.
-
Ogni altra apertura dei locali che contengono le cose assicurate nell’ubicazione indicata nella specifica sezione di
Polizza situata in linea verticale a meno di 4 metri dal suolo, da superfici d'acqua o da ripiani (come per esempio ballatoi, scale, terrazze e simili) accessibili e praticabili dall’esterno senza impiego di agilità personale o per mezzo di attrezzi, deve essere difesa da almeno uno dei mezzi sottoindicati:
a)
Serramenti di:
- legno pieno (legno sotto forma di tavole, pannelli truciolari e simili, il tutto anche a strati incollati tra di loro) dello spessore totale minimo di 20 mm, lamiera di acciaio dello spessore minimo di 1 mm (con o senza rivestimento di altro materiale). Tali Serramenti devono essere chiusi con serrature di sicurezza che azionano catenacci di adeguata robustezza e lunghezza o lucchetti di sicurezza o robusti catenacci manovrabili solo dall’interno e senza luci;
- vetro stratificato di sicurezza, il tutto totalmente fisso o chiuso con congegni (quali barre catenacci o simili) manovrabili esclusivamente dall’interno, oppure chiusi con serrature o lucchetti;
b) inferriate di:
```

### generali_immagina_adesso_p008_c02 | DIP aggiuntivo > A chi è rivolto questo prodotto? | pool=train_pool | 1543 chars
```
Rapina e Scippo fuori dall’Abitazione e Furto con destrezza della formula VIP: Somma assicurata indicata in Polizza. Per il denaro Scoperto 10% e massimo Indennizzo 3.500,00 euro.
A chi è rivolto questo prodotto?
Immagina Adesso - Modulo CASA è rivolto alle persone fisiche e ai loro nuclei familiari per la protezione degli immobili con caratteristiche costruttive previste per le abitazioni civili. Il Contraente può anche essere un’impresa o un ente. Il Modulo CASA si rivolge ai soggetti che hanno espresso:
• il bisogno di copertura relativo a Protezione dei beni e all’Assistenza e soccorso (Garanzie In solidità - Danni ai beni, Garanzie In guardia - Furto, Garanzie Prevenzione e Assistenza, Garanzia Pronto Avvocato);
• il bisogno di copertura relativo a Protezione del patrimonio e all’Assistenza e soccorso (Garanzie In solidità verso gli altri – Danni a terzi e Garanzie Prevenzione e Assistenza, Garanzia Pronto Avvocato);
• esclusivamente il bisogno di copertura relativo a Protezione dei beni (Garanzie In solidità - Danni ai beni) in caso di beni storici o in caso di polizze vincolate a garanzia di mutuo immobiliare con premio unico anticipato il cui onere è stato sostenuto dal cliente;
• il bisogno di copertura relativo a Protezione dei beni e Protezione del patrimonio (Garanzie In solidità - Danni ai beni e Garanzie In solidità verso gli altri - Danni a terzi) in caso di beni storici o in caso di polizze vincolate a garanzia di mutuo immobiliare con premio unico anticipato il cui onere è stato sostenuto dal cliente.
```

### generali_immagina_adesso_p017_c01 | DIP aggiuntivo > REGIME FISCALE | pool=train_pool | 1507 chars
```
Art. 1.2.2 Mezzi di protezione e chiusura per appartamento non su piano intermedio | 101
Art. 1.2.3 Mezzi di protezione e chiusura per villa non isolata | 102
Art. 1.2.4 Mezzi di protezione e chiusura per villa isolata | 104
Art. 1.3 Coesistenza di ufficio privato o studio professionale | 105
Che cosa è assicurato? Garanzie base | 105
Art. 2.1 Rischi assicurati | 105
Art. 2.2 Ulteriori spese indennizzabili | 106
Art. 2.3 Trasloco | 107
Art. 2.4 Condizione riservata alle abitazioni saltuarie | 107
Art. 2.5 Esclusione gioielli e preziosi | 107
Ci sono limiti di copertura? | 107
TABELLA RIASSUNTIVA FRANCHIGIE, SCOPERTI E LIMITI DI INDENNIZZO | 107
Che cosa è assicurato? Garanzie accessorie | 110
DEDICATO A TE | 110
CASA NATURA | 110
Art. 3.1 Furto impianto a energia rinnovabile | 110
CASA DI LUSSO | 110
Art. 3.2 Furto di gioielli e preziosi in cassette di sicurezza presso istituti di credito | 110
SPECIALE FAMIGLIA | 110
Art. 3.3 Truffa tra le mura domestiche | 111
Art. 3.4 Speciale Senior | 111
SPECIALE VIAGGIO E TEMPO LIBERO | 112
Art. 3.5 Furto del contenuto portato in altre abitazioni | 112
Art. 3.6 Estensione rapina e scippo al mondo intero | 112
SPECIALE PROFESSIONISTA | 112
Art. 3.7 Indennità aggiuntiva per presenza di attività commerciale | 112
PIÙ GENERALI | 112
Art. 3.8 Aumento della somma assicurata per festività natalizie e per matrimonio | 112
Art. 3.9 Furto commesso o agevolato, con dolo o colpa grave, dagli addetti ai servizi domestici e dai collaboratori familiari | 113
```

### generali_immagina_adesso_p041_c02 | Prevenzione e assistenza CASA > Casa Plus > Che cosa è assicurato? > Invio di un elettricista per interventi di emergenza | pool=validation_pool | 727 chars
```
Art. 1.2 Invio di un elettricista per interventi di emergenza
Che cosa è assicurato
In caso di guasto all’impianto dell’Abitazione, la Struttura Organizzativa invia all’Assicurato un elettricista.
Che cosa NON è assicurato
La Prestazione non è prevista in caso di:
- corto circuito per falsi contatti provocati dall’Assicurato;
- interruzione della fornitura elettrica da parte dell’ente fornitore;
- guasti al cavo di alimentazione dell’ente fornitore di pertinenza dell’abitazione.
Ci sono limiti di copertura
I costi di uscita e di manodopera sono a carico della Struttura Organizzativa fino a un massimo di 500,00 euro per Sinistro. Restano a carico dell'Assicurato i costi relativi ai materiali necessari alla riparazione.
```

### generali_immagina_adesso_p084_c02 | In solidità - Danni ai beni > Norme che operano in caso di sinistro | pool=train_pool | 1960 chars
```
Solo in caso di dolo, errori, violenza o di violazione dei patti contrattuali resta comunque possibile ogni azione o eccezione che riguarda l’indennizzabilità dei danni.
La perizia collegiale è valida anche se un perito si rifiuta di sottoscriverla; il rifiuto deve essere attestato dagli altri periti nel verbale definitivo di perizia. I periti sono dispensati dall’osservanza di ogni formalità di legge.
Art. 1.5 Determinazione del danno
La determinazione del danno è effettuata separatamente per ogni Partita indicata nella specifica sezione di Polizza. L’ammontare del danno indennizzabile è determinato:
•
Per l’Immobile, in base al Valore a nuovo. In caso di Sinistro, fermi i limiti e le Garanzie previsti nella specifica sezione di Polizza, sono liquidate le spese necessarie per ricostruire le parti distrutte o ripristinare quelle danneggiate. L’Indennizzo è tuttavia pagato inizialmente secondo il criterio del Valore allo stato d’uso. Il supplemento di Indennizzo a nuovo - pari alla differenza tra la stima dell’Indennizzo col criterio del Valore a nuovo e la stima dello stesso col criterio del Valore allo stato d’uso - è pagato solo quando l’Assicurato procede alla ricostruzione del Fabbricato. In caso contrario, non si procede al versamento del supplemento di Indennizzo a nuovo e il danno resta determinato e indennizzato secondo il criterio del Valore allo stato d’uso. In alternativa alla ricostruzione del Fabbricato, l’Assicurato può optare per l’acquisto di altra analoga abitazione. Quanto pagato da Generali Italia per l’acquisto non può comunque essere superiore al danno indennizzabile, determinato secondo il criterio del Valore a nuovo.
Per l’Impianto a energia rinnovabile, gli impianti di riscaldamento (per esempio Caldaie), di condizionamento e i
cancelli elettrici, l’ammontare del danno è determinato con il criterio:
-
del Valore a nuovo, per le cose per le quali non sono trascorsi più di 4 anni dalla data di acquisto;
-
```

### generali_immagina_adesso_p050_c03 | Prevenzione e assistenza CASA > Casa In Touch > Che cosa è assicurato? > In Touch gestione segnalazioni | pool=validation_pool | 1185 chars
```
Art. 1.16 In Touch gestione segnalazioni
Che cosa è assicurato
La corretta installazione e funzionamento del Kit Casa in Touch, come previsto dall’articolo Installazione Kit Casa in Touch delle NORME CHE OPERANO IN CASO DI SINISTRO e dalle Condizioni Generali di Abbonamento, attivano il servizio in Touch gestione segnalazioni. Quando il Kit Casa in Touch rileva con i relativi sensori, fumo, acqua al suolo, movimenti all’interno dell’Abitazione (solo se i sensori sono stati installati e attivati), o un’assenza prolungata di corrente elettrica nell’Abitazione, trasmette le segnalazioni all’Assicurato e alla Struttura di Supporto.
La Struttura di Supporto invia i dati necessari alla gestione della segnalazione alla Struttura Organizzativa che provvede a:
CASA IN TOUCH
- avvisare l’Assicurato ai contatti comunicati, tramite contatto telefonico, messaggio SMS, e-mail; il contatto telefonico, l’invio di SMS e di e-mail potranno essere effettuati solo se regolarmente funzionanti;
- contattare, in caso di irreperibilità dell’Assicurato, gli eventuali ulteriori nominativi ai contatti indicati dall’Assicurato;
- fornire le Prestazioni di assistenza previste dall'Assicurazione.
```

### generali_immagina_adesso_p103_c03 | In guardia - Furto Su misura Vip > Che cosa è assicurato? > Cose assicurate > Mezzi di protezione e chiusura per villa non isolata | pool=train_pool | 1701 chars
```
Art. 1.2.3 Mezzi di protezione e chiusura per villa non isolata
Mezzi di chiusura e di protezione dei locali
Che cosa è assicurato
LOCALI INCUSTODITI
Per l’indennizzabilità dei danni avvenuti nei locali, a eccezione di quelli da Rapina, quando gli stessi restano incustoditi, devono essere presenti le seguenti condizioni:
A) APERTURE VERSO L’ESTERNO
CASA - IN GUARDIA - SU MISURA VIP
•
Ogni ingresso dei locali che contengono le cose assicurate nell’ubicazione indicata nella specifica sezione di
Polizza deve essere difeso da Porta blindata chiusa con serratura.
•
Ogni altra apertura dei locali contenenti le cose assicurate nell’ubicazione indicata nella specifica sezione di Polizza
situata in linea verticale a meno di 4 metri dal suolo, da superfici d'acqua o da ripiani (come per esempio ballatoi, scale, terrazze e simili) accessibili e praticabili dall’esterno senza impiego di agilità personale o per mezzo di attrezzi,
deve essere difesa da almeno uno dei mezzi sottoindicati:
a)
Serramenti di:
- legno pieno (legno sotto forma di tavole, pannelli truciolari e simili, il tutto anche a strati incollati tra di loro) dello spessore totale minimo di 20 mm, lamiera di acciaio dello spessore minimo di 1 mm (con o senza rivestimento di altro materiale). Tali Serramenti devono essere chiusi con serrature di sicurezza che azionano catenacci di adeguata robustezza e lunghezza o lucchetti di sicurezza o robusti catenacci manovrabili esclusivamente dall’interno e senza luci;
- vetro stratificato di sicurezza, il tutto totalmente fisso o chiuso con congegni (quali barre catenacci o simili) manovrabili esclusivamente dall’interno, oppure chiusi con serrature o lucchetti;
b) inferriate di:
-
```

### generali_immagina_adesso_p039_c03 | Prevenzione e assistenza CASA > Casa Start > Come attivare l'assistenza | pool=validation_pool | 1485 chars
```
Art. 1.1 Come attivare l’assistenza
L’Assicurato può attivare tutte le Prestazioni solo dopo aver contattato la Struttura Organizzativa ai seguenti numeri:
dall’Italia al numero verde 800 880 880 dall’estero al numero +39 02 8295 1155
Quando richiede la Prestazione, l’Assicurato deve comunicare:
a) nome e cognome;
b) tipo di prestazione di cui ha bisogno;
c) numero di Polizza;
d) eventuale documentazione medica/veterinaria secondo il tipo di Garanzia sottoscritta;
e) indirizzo del luogo in cui si trova;
f) recapito telefonico dove può essere rintracciato nel corso dell’assistenza.
La Struttura Organizzativa può chiedere all’Assicurato anche il codice della fascia tessera indicato nella sezione Prevenzione e Assistenza della Polizza. Per fornire le Prestazioni previste dalla Garanzia ASSISTENZA CASA START, la Struttura Organizzativa deve effettuare il trattamento dei dati dell’Assicurato. Per questo motivo necessita del consenso dell’Assicurato, come previsto dalla normativa sulla protezione dei dati personali4. Nel momento in cui contatta o fa contattare la Struttura Organizzativa, l’Assicurato dà il consenso al trattamento dei suoi dati personali anche relativi alla salute e a reati e condanne penali se necessario, così come indicato nell’informativa dei dati ricevuta.
ASSISTENZA CASA START
4 GDPR General Data Protection Regulation – Regolamento UE 2016/679 e Decreto legislativo 30 giugno 2003 n. 196 e successive integrazioni e modifiche.
ASSISTENZA CASA START
```

### generali_immagina_adesso_p020_c01 | Presentazione Modulo | pool=train_pool | 1524 chars
```
GARANZIE BASE | GARANZIE ACCESSORIE | CONDIZIONI DI ATTIVAZIONE
IN SOLIDITÀ – DANNI AI BENI |  | 
CASA START |  | 
• Incendio e altri eventi per Immobile e/o Contenuto • Spese supplementari • Spese per modifiche costruttive al Fabbricato Trasloco • • Abitazione assicurata anche con polizza fabbricati civili di Generali Italia (se Incendio e altri eventi dell’Immobile) |  | Per l’Immobile alternativa a Rischio locativo
 | Ricorso terzi | Attivabile con Incendio e altri eventi
 | Rischio locativo | Alternativa a Incendio e altri eventi dell’Immobile se abitazione in affitto con Incendio e altri eventi del Contenuto
 | EVENTI STRAORDINARI | 
 | Eventi sociopolitici Guasti causati dai ladri e furto di fissi e infissi | Attivabile con Incendio e altri eventi
 | EVENTI NATURALI | 
 | Eventi atmosferici | Attivabile con Incendio e altri eventi
 | Grandine su fragili | Attivabile con Eventi atmosferici
 | Eventi atmosferici su impianti a energia rinnovabile | Attivabile con Grandine su fragili
 | Estensione alle tende frangisole dotate di anemometro | Attivabile con Eventi atmosferici
 | Sovraccarico di neve | Attivabile con Eventi atmosferici
 | Terremoto | Attivabile con Incendio e altri eventi dell’Immobile
 | Alluvione, Inondazione | Attivabile con Terremoto
 | Allagamento e Bombe d’acqua | Attivabile con Alluvione, Inondazione
 | IMPIANTO ELETTRICO | 
 | Fenomeni elettrici | Attivabile con Incendio e altri eventi
 | IMPIANTO IDRICO E TERMICO | 
 | Acqua condotta | Attivabile con Incendio e altri eventi
```

### generali_immagina_adesso_p046_c02 | Prevenzione e assistenza CASA > Casa Plus > Come attivare l'assistenza | pool=validation_pool | 1465 chars
```
Art. 1.1 Come attivare l’assistenza
L’Assicurato può attivare tutte le Prestazioni solo dopo aver contattato la Struttura Organizzativa ai seguenti numeri:
• dall’Italia al numero verde 800 880 880
• dall’estero al numero +39 02 8295 1155
Quando richiede la Prestazione, l’Assicurato deve comunicare:
a) nome e cognome;
b) tipo di prestazione di cui ha bisogno;
c) numero di Polizza;
d) eventuale documentazione medica/veterinaria secondo il tipo di Garanzia sottoscritta;
e) indirizzo del luogo in cui si trova;
f) recapito telefonico dove può essere rintracciato nel corso dell’assistenza.
La Struttura Organizzativa può chiedere all’Assicurato anche il codice della fascia tessera indicato nella sezione Prevenzione e Assistenza della Polizza. Per fornire le Prestazioni previste dalla Garanzia ASSISTENZA CASA PLUS, la Struttura Organizzativa deve effettuare il trattamento dei dati dell’Assicurato. Per questo motivo necessita del consenso dell’Assicurato, come previsto dalla normativa sulla protezione dei dati personali5. Nel momento in cui contatta o fa contattare la Struttura Organizzativa, l’Assicurato dà il consenso al trattamento dei suoi dati personali anche relativi alla salute e a reati e condanne penali se necessario, così come indicato nell’informativa dei dati ricevuta.
5 GDPR General Data Protection Regulation – Regolamento UE 2016/679 e Decreto legislativo 30 giugno 2003 n. 196 e successive integrazioni e modifiche.
ASSISTENZA CASA PLUS
```

### generali_immagina_adesso_p120_c03 | In guardia - Furto Tutto compreso Vip > Che cosa è assicurato? > Cose assicurate > Mezzi di protezione e chiusura per villa non isolata | pool=train_pool | 1670 chars
```
Art. 1.2.3 Mezzi di protezione e chiusura per villa non isolata
Mezzi di chiusura e di protezione dei locali
Che cosa è assicurato
LOCALI INCUSTODITI
Per l’indennizzabilità dei danni avvenuti nei locali, a eccezione di quelli da Rapina, quando gli stessi restano incustoditi devono essere presenti le seguenti condizioni:
A) APERTURE VERSO L’ESTERNO
-
Ogni ingresso dei locali che contengono le cose assicurate nell’ubicazione indicata nella specifica sezione di Polizza deve essere difeso da Porta blindata chiusa con serratura,
-
Ogni altra apertura dei locali che contengono le cose assicurate nell’ubicazione indicata nella specifica sezione di Polizza, situata in linea verticale a meno di 4 metri dal suolo, da superfici d'acqua o da ripiani (come per esempio ballatoi, scale, terrazze e simili) accessibili e praticabili dall’esterno senza impiego di agilità personale o per mezzo di attrezzi, deve essere difesa da almeno uno dei mezzi sotto indicati:
-
Serramenti di:
- legno pieno (legno sotto forma di tavole, pannelli truciolari e simili, il tutto anche a strati incollati tra di loro) dello spessore totale minimo di 20 mm, lamiera di acciaio dello spessore minimo di 1 mm (con o senza rivestimento di altro materiale). Tali serramenti devono essere chiusi con serrature di sicurezza che azionano catenacci di adeguata robustezza e lunghezza o lucchetti di sicurezza o robusti catenacci manovrabili esclusivamente dall’interno e senza luci;
- vetro stratificato di sicurezza, il tutto totalmente fisso o chiuso con congegni (quali barre catenacci o simili) manovrabili esclusivamente dall’interno, oppure chiusi con serrature o lucchetti;
-
Inferriate di:
•
```

### generali_immagina_adesso_p102_c01 | In guardia - Furto Su misura Vip > Che cosa è assicurato? > Cose assicurate > Mezzi di protezione e chiusura per appartamento su piano intermedio | pool=train_pool | 1216 chars
```
Se ci sono persone nell’abitazione, a deroga di quanto sopra indicato, l’Assicurazione opera nei termini previsti al successivo articolo Rischi assicurati.
In questo caso, se il Furto è commesso attraverso aperture protette da mezzi di protezione e chiusura che non rispondono alle caratteristiche di cui sopra o anche aperte e queste sono situate in linea verticale a meno di 4 metri dal suolo, da superfici d'acqua o da ripiani (come per esempio ballatoi, scale, terrazze e simili) accessibili e praticabili dall’esterno senza impiego di agilità personale o per mezzo di attrezzi, o l’impianto di allarme non è attivato:
• si applica uno Scoperto del 25%;
• il limite massimo di Indennizzo è di 50.000,00 euro.
Mezzi forti
Che cosa è assicurato
Per l’indennizzabilità dei danni avvenuti nei locali, a eccezione di quelli da Rapina, (anche se ci sono persone nei locali stessi) i Mezzi forti previsti per:
- le Partite Gioielli e preziosi in mezzi forti e Oggetti pregiati in mezzi forti devono essere costituiti da Cassaforte a muro,
se la somma nel complesso assicurata non è superiore a 100.000,00 euro, oppure Cassaforte;
- la Partita Raccolte e collezioni in mezzi forti devono essere costituiti da Cassaforte.
```

## zurich_impresa

### zurich_impresa_p150_c02 | Responsabilità Civile danni a terzi da prodotti (R.C.P.) > Che cosa è assicurato e come? > 7.6 Garanzie Premium (operanti solo se espressamente richiamate in Polizza) | pool=test_pool | 1860 chars
```
4) pretese o responsabilità per danni decretati dal tribunale a scopo punitivo o di ammonimento del responsabile.
L’Assicurazione non vale per qualsiasi persona o organizzazione dalla quale l’Assicurato Contraente abbia acquisito prodotti o componenti, parti di essi o contenitori che fanno parte del prodotto cui si riferisce la garanzia.
AVVERTENZA
Il testo della presente garanzia è riportato anche in lingua inglese per utilità dell’Assicurato, ma il contratto è disciplinato dal testo italiano.
Additional Insured (Vendors Limited Form)
This endorsement modifies such insurance as is afforded by the provisions of the policy relating to the following products liability insurance. It is agreed that the “Person Insured” provision is amended to include any person or organization designated below (herain referred to as “vendor”), as an insured, but only with respect to the distribution or sale in the regular course of the vendor’s business of the named insured’s products covered under said policy. The insurance does not apply to:
a) any express warranty, or any distribution or sale for a purpose, unauthorized by the named insured;
b) bodily injury or property damage arising out of:
I. any act of the vendor which changes the condition of the products,
II. any failure of the vendor to maintain the product in merchantable condition,
III. any failure of the vendor to make such inspections, adjustements, tests or servicing as the vendor itself has agreed to make
or normally untertakes to make in the usual course of business, in connection with the distribution or sale of the products,
IV. products which after distribution or sale by the named insured have been labeled or relabeled or used as a container, part
or ingredient of any other thing or substance by or for the vendor;
c) bodily injury or property damage within the vendor’s premises;
```

### zurich_impresa_p023_c01 | DIP aggiuntivo > Che cosa è assicurato? > RESPONSABILITA’ CIVILE DANNI A TERZI | pool=test_pool | 1331 chars
```
 | B) Lavori edili La presente garanzia vale per la Responsabilità Civile derivante all’assicurato, ai sensi di Legge, nello svolgimento dell’attività edile descritta in polizza per danni cagionati a terzi (compresi i Committenti) avvenuti dopo la data di ultimazione dei lavori, esclusivamente in conseguenza di difettosa esecuzione degli stessi. Per data di ultimazione dei lavori si intende: • sottoscrizione del verbale di ultimazione dei lavori o rilascio di certificato provvisorio di collaudo; • consegna anche provvisoria o temporanea dell’opera al committente; • uso anche parziale o temporaneo dell’opera secondo destinazione. L’assicurazione vale esclusivamente per i lavori eseguiti in immobili adibiti ad uso civile, ad attività produttive, al commercio, al terziario, nonché per i lavori di scavo e reinterro. Norme comuni alle attività di cui ai punti A) e B): In caso di sostituzione con altra polizza R.C.T. emessa con la presente Compagnia, purché senza soluzione di continuità, e sempreché rimanga operante la presente garanzia postuma, l’assicurazione vale anche per i danni verificatisi e denunciati durante il periodo di validità della polizza sostituente conseguenti a lavori eseguiti durante il periodo di validità della presente polizza, fermo restando il limite temporale dalla data di termine dei lavori.
```

### zurich_impresa_p036_c01 | DIP aggiuntivo > Che cosa NON è assicurato? > Civile danni a terzi | pool=test_pool | 1916 chars
```
Merci in refrigerazione | Sono esclusi i danni dovuti a difetto di manutenzione, vizio di progettazione o costruzione degli impianti di refrigerazione.
Eventi Atmosferici | Sono esclusi i danni causati da: a) bagnamento delle merci, poste in locali interrati e seminterrati, collocati ad altezza inferiore a 10 centimetri dal suolo, salvo quelle che per le loro particolari caratteristiche merceologiche non possono essere appoggiate su pallets; b) acqua o grandine penetrata attraverso finestre o lucernari lasciati aperti, o aperture prive di protezione; c) intasamento o traboccamento di gronde o pluviali con o senza rottura degli stessi; d) infiltrazioni, umidità, stillicidio, corrosione, usura; e) formazione di ruscelli; accumulo esterno di acqua; rottura, rigurgito o traboccamento dei sistemi di scarico; f) inondazioni, alluvioni, slavine, valanghe, mareggiate, penetrazioni di acqua marina; g) gelo, sovraccarico di neve; h) cedimento o franamento del terreno ancorché verificatisi a seguito degli eventi atmosferici di cui sopra subiti da: i) recinzioni, cancelli, gru, cavi aerei, insegne o antenne e simili installazioni esterne; j) serre e alle altre “Cose assicurate” in esse contenute; k) tende da sole, tettoie, tendoni, tendalini, zanzariere, veneziane installati all’esterno del fabbricato; l) collettori solari; m) palloni pressostatici, strutture geodetiche, tendostrutture, tensostrutture, baracche in legno o plastica e quanto in esse contenuto; n) gazebo, dehors, bersò e verande; o) fiori, alberi, piante e coltivazioni in genere; p) merci, macchinari, attrezzature, arredamento posti all’aperto oppure sotto fabbricati aperti su uno o più lati, ad eccezione di serbatoi e impianti fissi per natura e destinazione; q) fragili quali: lastre di cemento-amianto o di fibrocemento, manufatti di materia plastica, lastre dei serramenti, vetrate e Lucernari in genere per effetto della grandine.
```

### zurich_impresa_p009_c03 | DIP aggiuntivo > Che cosa è assicurato? > Eventi assicurati | pool=test_pool | 1757 chars
```
5) dal servizio di vigilanza effettuato con guardiani anche armati e dalla detenzione di cani; 6) dalla proprietà, uso, installazione e manutenzione di insegne luminose e non, di cartelli pubblicitari e striscioni, ovunque installati nel territorio italiano. L’assicurazione non comprende i danni alle opere ed alle cose sulle quali sono applicate le insegne, i cartelli e gli striscioni; 7) dalla circolazione ed uso, anche all’esterno dei complessi aziendali, di velocipedi, mezzi di trasporto a mano e ciclofurgoncini senza motore; 8) dal servizio antincendio interno o da intervento diretto di prestatori di lavoro dell’assicurato per tale scopo; 9) dalla proprietà, manutenzione ed esercizio di cabine elettriche e/o centrali energetiche di trasformazione e/o produzione, serbatoi di carburante, nonché i relativi impianti e reti di distribuzione all’interno dell’azienda; 10) dall’organizzazione di visite all’azienda e dalla presentazione e/o dimostrazione dei prodotti e/o dei cicli di lavorazione dell’azienda stessa, anche presso terzi; 11) dalla proprietà e/o conduzione di colonie ed asili nido per i figli dei prestatori di lavoro; 12) dalla proprietà e dall’uso di binari di raccordo e piattaforme rotanti, inclusi i danni provocati a materiale rotabile di terzi; 13) a veicoli di terzi e di prestatori di lavoro in sosta entro l’area di pertinenza aziendale ove si svolgono le attività assicurate o trovantisi nell’ambito di esecuzione dei lavori. Sono esclusi i danni da furto, incendio e atti dolosi in genere, nonché i danni da mancato uso o disponibilità del veicolo; 14) dal servizio di pulizia dei locali occupati dall’assicurato per l’esercizio dell’attività descritta in polizza, comprese le aree esterne di pertinenza del fabbricato;
```

### zurich_impresa_p022_c03 | DIP aggiuntivo > Che cosa è assicurato? > RESPONSABILITA’ CIVILE DANNI A TERZI | pool=test_pool | 1415 chars
```
Malattie professionali | La garanzia è estesa al rischio delle malattie professionali, intendendo per queste oltre a quelle indicate nelle tabelle, in vigore al momento della polizza, allegate al Decreto del Presidente della Repubblica 30/06/1965 n. 1124 e successive modificazioni, anche le altre malattie professionali che sono riconosciute tali a livello giudiziale ed in nesso di causa con l’attività assicurata in polizza.
Smercio | L’assicurazione vale per la Responsabilità Civile derivante all’assicurato ai sensi di legge per i danni cagionati a terzi (per morte, per lesioni personali e per danni a cose), ivi compreso l’acquirente, causati dalle cose vendute, esclusi quelli dovuti a vizio originario del prodotto. Per i generi alimentari di produzione propria, somministrati o venduti negli spacci aziendali, nei negozi situati nell’ambito dell’azienda durante esposizioni, fiere, mostre e mercati e durante l’attività promozionale o offerti in degustazione, l’assicurazione vale anche per i danni dovuti a vizio originario del prodotto. L’assicurazione riguarda i danni verificatisi entro un anno dalla consegna e, comunque, non oltre la data di scadenza della polizza, da cose vendute durante il periodo di validità della garanzia e non comprende i danneggiamenti delle cose stesse, le spese per le relative riparazioni o sostituzioni, nonché i danni conseguenti a mancato uso o mancata disponibilità.
```

### zurich_impresa_p092_c01 | Incendio e Danni ai beni > Che cosa è assicurato e come? > 2.8 Garanzie Premium per tutte le ubicazioni (operanti solo se espressamente richiamate in Polizza) | pool=test_pool | 1783 chars
```
1) l’uso di macchine o impianti in sostituzione di quelli danneggiati o distrutti;
2) il lavoro straordinario, anche notturno o festivo, del personale;
3) le lavorazioni presso terzi;
4) la fornitura di energia elettrica o termica da parte di terzi;
5) gli affitti di locali per il trasferimento temporaneo dell’attività compresi i relativi costi di trasferimento.
La Compagnia non risponde delle maggiori spese conseguenti a prolungamento ed estensione dell’inattività causati da:
a) scioperi, tumulti popolari, sommosse, serrate, provvedimenti imposti dall’Autorità, stati di guerra;
b) difficoltà di reperimento delle Merci, dei macchinari, delle attrezzature o degli impianti imputabili a cause esterne, quali
a titolo esemplificativo e non limitativo, disastri naturali, scioperi che impediscano o rallentino le forniture, stati di guerra, regolamenti urbanistici locali o statali o altre norme di legge o provvedimenti dell’Autorità.
Non sono indennizzabili spese sostenute successivamente alla scadenza del periodo di Indennizzo. Per periodo di Indennizzo si intende il periodo strettamente necessario per la riparazione o il rimpiazzo delle “Cose assicurate” (def. al punto 2.4) danneggiate o distrutte, e che avrà durata massima di tre mesi dal verificarsi del Sinistro.
2.8.5 Diaria da interruzione di attività
La Compagnia indennizza l’Assicurato delle perdite determinata da interruzione totale o parziale dell’attività causata da un Sinistro indennizzabile ai sensi della sezione “Incendio e danni ai beni”. Per i giorni durante i quali l’inattività è solo parziale la Diaria è ridotta in proporzione. Oltre a quanto previsto al punto 2.9 “Esclusioni valide per tutte le garanzie” del capitolo “Che cosa non è assicurato?”, per quanto non derogato, sono esclusi i danni:
```

### zurich_impresa_p120_c03 | Responsabilità Civile della proprietà del fabbricato > Che cosa è assicurato e come? > 5.6 Garanzie Premium (operanti solo se espressamente richiamate in Polizza) | pool=test_pool | 1765 chars
```
5.6 Garanzie Premium (operanti solo se espressamente richiamate in Polizza)
5.6.1. Responsabilità Civile verso Prestatori di lavoro (R.C.O.)
La Compagnia si obbliga a tenere indenne l’Assicurato di quanto questi sia tenuto a pagare, quale civilmente responsabile ai sensi di legge, a titolo di Risarcimento (capitale, interessi e spese) di danni per morte e per lesioni personali in conseguenza di Infortuni sul lavoro, escluse le Malattie professionali, sofferti da “Prestatori di lavoro” preposti alle attività relative ai fabbricati per i quali è prestata l’Assicurazione. L’Assicurazione vale anche per le azioni intraprese da:
1. I.N.A.I.L. ai sensi degli articoli 10 e 11 del Decreto del Presidente della Repubblica 30/06/1965 n. 1124 e successive modifiche nonché per gli effetti del Decreto legislativo n. 23/2/2000 n. 38;
2. I.N.P.S. ai sensi dell’art. 14 della Legge 222 del 12/6/1984 e successive modifiche. L’Assicurazione è efficace a condizione che al momento del Sinistro:
• qualora l’obbligo di corrispondere il Premio assicurativo all’I.N.A.I.L. ricada in tutto o in parte sull’Assicurato, lo stesso sia in regola con gli obblighi dell’Assicurazione di legge; qualora tuttavia l’irregolarità derivi da errate interpretazioni delle norme di legge vigenti in materia, l’Assicurazione conserva la propria validità;
• il rapporto o la prestazione di lavoro si svolga nel rispetto della vigente legislazione in materia; qualora tuttavia l’irregolarità derivi da errate interpretazione delle norme vigenti in materia, l’Assicurazione conserva la propria validità.
La garanzia è prestata entro il limite del Massimale e con l’applicazione della Franchigia previsti in Polizza.
La garanzia Responsabilità Civile Prestatori di lavoro opera nel mondo intero.
```

### zurich_impresa_p039_c04 | DIP aggiuntivo > Che cosa NON è assicurato? > Elettronica | pool=test_pool | 1155 chars
```
Allagamento | Sono esclusi i danni: a) causati da inondazione e alluvione; b) causati da mareggiata, marea, maremoto e penetrazione di acqua marina; c) causati dalla fuoriuscita d’acqua da impianti automatici di estinzione; d) causati da gelo, umidità, stillicidio, trasudamento, infiltrazione, ancorché conseguenti all’evento coperto dalla presente garanzia; e) causati da mancata o anormale produzione o distribuzione di energia elettrica, termica o idraulica, salvo che tali circostanze siano connesse al diretto effetto dell’inondazione o dell’alluvione sulle “Cose assicurate”; f) da franamento, cedimento o smottamento del terreno; g) alle cose all’aperto; h) avvenuti a seguito di rotture, brecce o lesioni provocate al Tetto, alle pareti o ai Serramenti dal vento o dalla grandine; i) da rottura di contenitori; j) alle merci poste ad un’altezza inferiore a 10 cm dal pavimento o suolo salvo quelle che per le loro particolari caratteristiche merceologiche non possano essere appoggiate su pallets. k) causati da pioggia, grandine, neve, penetrate nei fabbricati attraverso aperture che non siano state chiuse da serramenti al momento del Sinistro
```

### zurich_impresa_p071_c04 | Norme comuni a tutte le garanzie > Che obblighi ho? > 1.3 Buona fede | pool=test_pool | 1059 chars
```
1.3 Buona fede
Se le inesattezze e omissioni descritte ai punti precedente (1.1 e 1.2) non riguardano le caratteristiche essenziali e durevoli del Rischio e il Contraente/Assicurato ha agito in buona fede, senza dolo o colpa grave, il Contraente/Assicurato mantiene per intero il diritto all’Indennizzo ma la Compagnia ha il diritto di percepire l’incremento di Premio corrispondente al maggior Rischio a decorrere dal momento in cui la circostanza aggravante si è verificata.
1.4 In caso di diminuzione del Rischio
Si ha diminuzione del Rischio quando nel corso del contratto la probabilità che si verifichi un Sinistro diminuisce. Anche in questo caso è necessaria la comunicazione tramite raccomandata con ricevuta di ritorno alla Compagnia o posta elettronica certificata (PEC), che procederà alla riduzione del Premio a decorrere dal giorno successivo all’avvenuta notifica e rimborserà la corrispondente quota di Premio imponibile pagata e non goduta. La Compagnia rinuncia al diritto di recedere dal contratto previsto dall’art. 1897 del Codice civile.
```

### zurich_impresa_p173_c03 | Assistenza > Che cosa è assicurato e come? > 9.4 Prestazioni | pool=test_pool | 1513 chars
```
L’Assicurato verrà messo direttamente in contatto con uno dei medici della Struttura Organizzativa al fine di far valutare il proprio stato di salute e di ricevere le prime indicazioni su quale sia la cura più idonea da seguire. Si precisa che tale Prestazione, considerate le modalità di Prestazione del servizio, non costituisce diagnosi ed è prestata sulla base delle informazioni e dichiarazioni fornite a distanza dall’Assicurato.
• La Prestazione è operante da lunedì al venerdì dalle ore 8:00 alle ore 20:00, esclusi i festivi infrasettimanali.
La Compagnia terrà a proprio carico il relativo costo.
9.4.15 Invio di un medico in caso d’urgenza
Qualora l’Assicurato, a seguito di Infortunio, necessiti di un medico generico dalle ore 20:00 alle ore 8:00 nei giorni feriali o nei giorni
festivi e non riesca a reperirlo, potrà contattare la Struttura Organizzativa che, organizzerà l’invio di un medico presso il Fabbricato. Nell’eventualità in cui il medico non riesca ad intervenire personalmente, la Struttura Organizzativa predisporrà, in via sostitutiva, il trasferimento dell’Assicurato nel centro medico idoneo a lui più vicino, mediante il mezzo di trasporto più indicato rispetto alle sue condizioni di salute.
La Compagnia terrà a proprio carico il costo dell’invio del medico e della visita medica o del mezzo di trasporto utile al trasferimento entro il Massimale di 200 Euro per Sinistro.
Restano a carico dell’Assicurato i costi delle cure, degli esami, delle ulteriori visite e delle medicine.
```

### zurich_impresa_p103_c02 | Furto > Che cosa è assicurato e come? > 3.7 Garanzie Premium (operanti solo se espressamente richiamate in Polizza) | pool=test_pool | 1682 chars
```
Qualora un veicolo (o natante) sottratto o danneggiato fosse già assicurato con altra polizza diretta stipulata dal singolo proprietario (o da altri nell’interesse e per conto dello stesso), la presente garanzia è operante esclusivamente per la parte eventualmente rimasta scoperta da tale assicurazione senza applicazione di alcun scoperto e relativo minimo. L’assicurazione opera anche per l’eventuale azione di rivalsa esperita dall’assicuratore del veicolo (o natante) nei confronti dell’Assicurato, fermo il Limite di indennizzo per veicolo o per Sinistro previsto.
Questa garanzia è prestata nella forma a Primo Rischio Assoluto e prevede l’applicazione dello Scoperto e del Limite di indennizzo indicati in Polizza.
3.7.3 Impianto fotovoltaico
La garanzia è estesa ai danni di Furto dei pannelli dell’Impianto fotovoltaico indicato in Polizza, al servizio esclusivo dell’Azienda assicurata. Sono inclusi i danni derivanti da guasti cagionati dai ladri per commettere il Furto o per tentare di commetterlo.
La garanzia è prestata a condizione che l’Impianto fotovoltaico sia installato sulle coperture dei Fabbricati dell’Azienda e che sia dotato di almeno una delle seguenti caratteristiche:
• bulloni destinati all’ancoraggio dei pannelli ai relativi sostegni di tipo “antifurto” o che prevedano un sistema che ne impedisca la rimozione con sistemi ordinari;
• pannelli vincolati mediante incollaggio ai relativi supporti;
• presenza di impianto antifurto di localizzazione GPS o collegato in remoto con istituto di vigilanza privato;
• presenza di Impianto di videosorveglianza o di Impianto di allarme collegato a stazione di controllo o guardiania operativa 24 ore su 24.
```

### zurich_impresa_p037_c02 | DIP aggiuntivo > Che cosa NON è assicurato? > riparazione e | pool=test_pool | 640 chars
```
riparazione e
ripristino
Sono esclusi i danni:
a) alle apparecchiature elettroniche;
b) a lampadine e altre fonti di luce, valvole termoelettroniche, resistenze scoperte e fusibili, batterie e
accumulatori;
c) causati da usura, corrosione, logorio;
d) riconducibili a mancata o difettosa manutenzione, manomissione o uso inappropriato;
e) agli impianti di erogazione di energia elettrica e telefonici di proprietà delle aziende erogatrici;
f) agli impianti di irrigazione, ad accezione delle centraline poste all’interno dei fabbricati;
g) verificatisi in occasione di montaggi e smontaggi non connessi a lavori di manutenzione o revisione,
```

### zurich_impresa_p020_c02 | DIP aggiuntivo > Che cosa è assicurato? > INCENDIO E DANNI AI BENI | pool=test_pool | 1465 chars
```
Indennità aggiuntiva a percentuale | A parziale deroga delle condizioni generali di assicurazione, l’indennizzo, calcolato per ciascuna partita separatamente, sarà maggiorato, sino alla concorrenza del 10% dell’indennizzo stesso, di un importo a titolo di rimborso per le spese necessarie, debitamente documentate, per il proseguimento dell’attività, sempreché tali spese siano sostenute durante il periodo di indennizzo e riguardino a titolo esemplificativo: 1. l’uso di macchine o impianti in sostituzione di quelli danneggiati o distrutti; 2. il lavoro straordinario, anche notturno o festivo, del personale; 3. le lavorazioni presso terzi; 4. la fornitura di energia elettrica o termica da parte di terzi; 5. gli affitti di locali per il trasferimento temporaneo dell’attività compresi i relativi costi di trasferimento.
Diaria da interruzione di attività | La Compagnia indennizza l’assicurato delle perdite determinata da interruzione totale o parziale dell’attività causata da un sinistro indennizzabile ai sensi della sezione “Incendio e danni ai beni”. Per i giorni durante i quali l’inattività è solo parziale la Diaria è ridotta in proporzione. La garanzia è sospesa in caso di inattività dell’azienda per cause diverse da quelle previste, e si riattiva al momento in cui l’attività viene in tutto o in parte ripresa. Quando l’inattività dell’azienda sia parziale, l’assicurazione vale solo per la parte dell’esercizio che continua ad essere in attività.
```

### zurich_impresa_p071_c01 | Norme comuni a tutte le garanzie | pool=test_pool | 1439 chars
```
Norme comuni a tutte le garanzie
Avvertenza
Si richiama l’attenzione del Contraente/Assicurato sulle clausole evidenziate in grassetto che prevedono decadenze, nullità, esclusioni, sospensioni e limitazioni delle garanzie, oppure oneri e obblighi a carico del Contraente/Assicurato.
Che obblighi ho?
1.1 Dichiarazioni del Contraente
Il Contraente e l’Assicurato devono indicare alla Compagnia tutti gli aspetti che possono influire sulla valutazione del Rischio. La violazione di questo obbligo può comportare serie conseguenze. Gli articoli 1892 e 1893 del Codice Civile prevedono, infatti, che:
• le dichiarazioni inesatte o reticenti rese con dolo o colpa grave su circostanze che il Contraente o l’Assicurato conoscono o che, facendo uso della normale diligenza, potrebbero conoscere, sono causa di annullamento del contratto e possono comportare la perdita totale del diritto all’Indennizzo. In questo caso, la Compagnia ha diritto a chiedere l’annullamento del contratto, a condizione che lo abbia comunicato al Contraente entro tre mesi dalla scoperta di tali dichiarazioni (cfr. art. 1892 c.c.). Se il Sinistro si verifica prima che sia decorso il termine di tre mesi sopra indicato, la Compagnia non è tenuta a pagare la somma assicurata. In ogni caso la Compagnia ha diritto a trattenere il Premio convenuto per il primo anno e ai Premi relativi al Periodo di Assicurazione in corso al momento in cui ha domandato l’annullamento;
```

### zurich_impresa_p014_c03 | DIP aggiuntivo > Che cosa è assicurato? > Danni da inquinamento | pool=test_pool | 1475 chars
```
Tale garanzia è operante esclusivamente per le conseguenze direttamente causate dall’evento dannoso e non per le sue conseguenze indirette come mancato uso e interruzioni di esercizio.
Danni da inquinamento
accidentale
Danni da incendio
In relazione al prodotto “Estintori, apparecchiature antincendio”, l’assicurazione vale, per i danni da incendio conseguenti a rottura dei prodotti descritti in polizza.
TUTELA LEGALE
Sono previste due forme di garanzia:
Forma Base: si assicura l’assistenza giudiziale che si renda necessaria a tutela dei diritti dell’assicurato nell’ambito dell’attività di azienda dichiarata in polizza, e nella conduzione e/o proprietà degli immobili dove viene svolta l’attività, indicati in polizza.
La garanzia vale esclusivamente nel caso in cui l’assicurato:
a) sia sottoposto a procedimento penale per delitto colposo o per contravvenzione, compresi i procedimenti
derivanti da violazioni in materia fiscale ed amministrativa,
b) sia sottoposto a procedimento penale per delitto doloso, compreso quello derivante da violazioni in materia
fiscale ed amministrativa, se si verifica una delle seguenti condizioni:
• l’assicurato venga prosciolto o assolto con decisione passata in giudicato,
• sia intervenuta archiviazione per infondatezza della notizia di reato, ai sensi dell’art. 408 del Codice di Procedura Penale, o per applicazione della pena su richiesta delle parti (patteggiamento);
• il reato sia derubricato da delitto doloso a colposo.
```

### zurich_impresa_p097_c01 | Incendio e Danni ai beni > Come è gestito il Sinistro? > 2.12 Mandato dei periti | pool=test_pool | 888 chars
```
delle valutazioni di cui ai punti c) e d), che non potranno essere contestati se non in caso di dolo, errore, violenza o violazione dei patti contrattuali. Lo svolgimento delle operazioni peritali consente, tuttavia, azioni ed eccezioni relative all’indennizzabilità dei danni. La perizia collegiale è valida anche se un perito si rifiuta di sottoscriverla; tale rifiuto deve essere attestato dagli altri periti nel verbale definitivo di perizia. I periti non sono tenuti all’osservanza di particolari formalità.
2.13 Svolgimento delle operazioni peritali
In caso di Sinistro che colpisca uno o più reparti dell’Ubicazione assicurata, le operazioni peritali verranno impostate e condotte in modo da non pregiudicare per quanto possibile l’attività, anche se ridotta, svolta nelle aree non direttamente interessate dal Sinistro o nelle stesse porzioni utilizzabili dei reparti danneggiati.
```

### zurich_impresa_p007_c01 | DIP aggiuntivo > Che cosa è assicurato? > Eventi assicurati | pool=test_pool | 1254 chars
```
Errori di manovra e movimentazione | La garanzia comprende i danni alle “Cose assicurate” causati da errori di manovra e movimentazione nell’utilizzo di mezzi o veicoli non iscritti al P.R.A. La garanzia vale esclusivamente per i danni avvenuti all’interno del perimetro aziendale dell’ubicazione indicata in polizza e all’esterno, entro il limite di 20 metri dal perimetro stesso, purché il veicolo sia utilizzato per operazioni di carico/scarico. La garanzia prevede: • la franchigia di 500 Euro per sinistro; • il limite massimo di indennizzo di 2.500 Euro a primo rischio assoluto per sinistro e anno assicurativo.
Trasloco | In caso di trasloco/trasferimento, l’assicurazione vale anche nella nuova ubicazione, fermo il disposto dell’art. 1898 del Codice civile in caso di aggravamento di rischio, a condizione che sia ubicata nel territorio italiano, previa comunicazione scritta alla Compagnia o all’intermediario assicurativo da effettuarsi tramite lettera raccomandata o posta elettronica certificata (PEC). Alle ore 24 del 30° giorno successivo al ricevimento della comunicazione, l’assicurazione cessa nei confronti della vecchia ubicazione e opera esclusivamente per la nuova, fino alla prima scadenza utile per l’aggiornamento della polizza.
```

### zurich_impresa_p107_c01 | Furto > Che cosa è assicurato e come? > 3.11 Garanzie Premium (operanti solo se espressamente richiamate in polizza) | pool=test_pool | 1780 chars
```
Il Contraente dichiara che i locali, contenenti le “Cose assicurate” (def. al punto 3.8), dell’Ubicazione assicurata in Polizza e oggetto di Furto, sono protetti da impianto automatico di allarme antifurto realizzato a regola d’arte, ovvero che sia in possesso di una dichiarazione di conformità, rilasciata da un tecnico abilitato, a quanto previsto dal Decreto 22 gennaio 2008, n. 37 (e successive integrazioni). L’Assicurato si impegna a mantenere detti impianti in perfetta efficienza e ad attivarlo ogni qualvolta nei suddetti locali non vi sia presenza di persone. Qualora in caso di Sinistro risultasse che l’impianto di allarme fosse inefficiente per motivi diversi da:
a) manomissione da parte degli autori del Furto;
b) evento accidentale ed esterno che abbia colpito l’impianto dopo la sua attivazione e che abbia provocato un guasto
all’impianto stesso. Il periodo di guasto dell’impianto non può superare le 48 ore.
La Compagnia corrisponderà l’80% dell’importo liquidabile a termini delle Condizioni di Assicurazione, restando il 20% rimanente a carico dell’Assicurato stesso senza che egli possa, sotto pena di decadenza da ogni diritto all’Indennizzo, farlo assicurare da altri. In caso di applicabilità di più Scoperti le percentuali dei medesimi vengono unificate nella misura massima del 40%.
3.11.5 Mezzi di protezione rinforzati comune
L’Assicurazione è prestata a condizione che ogni apertura verso l’esterno dei locali contenenti le “Cose assicurate” (def. al punto 3.8), dell’Ubicazione assicurata in Polizza e oggetto di Furto, situata in linea verticale a meno di 4 metri:
• dal suolo;
• da superfici acquee;
• da ripiani accessibili e praticabili per via ordinaria dall’esterno, senza impiego cioè di mezzi artificiosi o di particolare agilità personale
```

### zurich_impresa_p009_c01 | DIP aggiuntivo > Che cosa è assicurato? > Eventi assicurati | pool=test_pool | 985 chars
```
Oggetto dell’Assicurazione | La Compagnia si obbliga a tenere indenne l’assicurato di quanto questi sia tenuto a pagare, quale civilmente responsabile ai sensi di legge, a titolo di risarcimento (capitale, interessi e spese) di danni involontariamente cagionati a terzi, per morte, per lesioni personali e per danni materiali a cose, in conseguenza di un Sinistro verificatosi in relazione all’attività descritta in polizza. Sono compresi i rischi derivanti dalle attività complementari e accessorie. L’assicurazione vale anche per la Responsabilità Civile che possa derivare all’assicurato: • per fatto doloso di persone delle quali debba rispondere; • per le azioni di rivalsa esperite dall’I.N.P.S. ai sensi dell’articolo 14) della Legge 12 Giugno 1984, n. 222 e successive modifiche, nonché per le azioni di rivalsa esperite da I.N.A.I.L. e da parte di qualsiasi altro Ente previdenziale o assistenziale. Le garanzie sono prestate entro il limite del massimale indicato in polizza.
```

### zurich_impresa_p156_c01 | Responsabilità Civile danni a terzi da prodotti (R.C.P.) > Cosa fare in caso di Sinistro? > 7.8 Denuncia di Sinistro | pool=test_pool | 1672 chars
```
k) licenze autorizzative concernenti le attività accessorie (se pertinente con la dinamica del Sinistro);
l) titolo abilitativo sia del Responsabile della sicurezza dei lavoratori, sia del Responsabile del Servizio di Prevenzione e Protezione (se pertinente con la dinamica del Sinistro);
m) certificazione medica attestante la stabilizzazione dei postumi o l’invalidità temporanea riportata in caso di lesioni fisiche (se
pertinente con la dinamica del Sinistro);
n) autocertificazione attestante lo stato di famiglia (se pertinente con la dinamica del Sinistro);
o) denuncia dell’Infortunio a I.N.A.I.L. e documentazione attestante la regolarità del rapporto di lavoro (se pertinente con la dinamica
del Sinistro);
p) diffide/Rivalse I.N.A.I.L. (se pertinente con la dinamica del Sinistro);
q) documentazione inerente all’inquadramento del lavoratore (busta paga e indicazione della mansione svolta); (se pertinente con la
dinamica del Sinistro);
r) documentazione inerente alla formazione dell’infortunato e attestazione dell’espletamento dei relativi obblighi di legge (copia
attestati di formazione e informazione del lavoratore nonché ricevuta di consegna DPI); (se pertinente con la dinamica del Sinistro);
s) piano di Sicurezza e Copia DUVRI (se presenti); (se pertinente con la dinamica del Sinistro);
t) libro Unico del Lavoro (se pertinente con la dinamica del Sinistro).
Inoltre, su richiesta motivata della Compagnia, potranno essere richiesti ulteriori specifici documenti (come previsto al punto 7.9 “Tempi di gestione del Sinistro”).
La denuncia e i documenti devono essere consegnati o inviati direttamente all’Intermediario assicurativo o alla Compagnia.
```
