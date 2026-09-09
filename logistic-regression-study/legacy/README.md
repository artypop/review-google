# Legacy — fichiers remplacés de l'étude de régression

Rien ici ne doit être exécuté ni cité. Conservé pour la trace.

| Fichier | Remplacé par | Pourquoi |
|---|---|---|
| `04_avis_features.sql`, `04_avis_features-v2.sql` | `../sql/04_avis_features-v3.sql` | `WHERE NOT is_update` ne rendait pas une ligne par avis : 617 avis en double, ceux qui ont disparu puis sont revenus. La v3 dédoublonne et ajoute `author_key`. |
| `05_panel_final.sql`, `05_panel_final-v2.sql` | `../sql/05_panel_final-v3.sql` | Joignaient deux tables non dédoublonnées, donc chaque avis concerné sortait multiplié par 4 à chaque vague : 17 858 lignes en trop et 766 suppressions comptées deux fois. |
| `06_statsmodels_analysis.py` | `../06_statsmodels_analysis_review_claude.py` | Chargeait 63 millions de lignes en `SELECT *`, ce qui faisait planter la machine. Fabriquait 15 000 lignes aléatoires quand BigQuery ne répondait pas, et imprimait des coefficients d'allure crédible. Prenait les 24 plus gros compteurs de suppressions pour les « 24 fiches », ce qui n'est pas la définition du projet. |

Détail des corrections dans `../BACKLOG.md`, section « Fait le 2026-09-09 ».
