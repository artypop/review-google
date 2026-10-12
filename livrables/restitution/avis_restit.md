\- 65 % des avis ont un texte sur toute la base, 73 % sur le corpus 180 jours.







\- La référence est un avis type : 5 étoiles, sans texte, niveau Local Guide 1 à 4, automobile, un seul établissement. Ce n'est pas un avis moyen.







\- Le modèle suppose que chaque effet est le même quel que soit l'avis de départ. Changer la référence de la note (3 ou 5 étoiles) ne change que les lignes de la note : le Local Guide, le secteur et la photo gardent exactement les mêmes chiffres.





\- « Il faut compter 30 % de retirés » dans l'antiparasitaire (08:54). Dans nos données, 11,5 % des avis antiparasitaires publiés en août 2026 ont été supprimés.



\- Niveau 0 local guide : existe par contre sans niveau ça n'existe pas ? pas vraiment ça existe pas c'est juste que ce n'est pas renseigné -> pourquoi ?





\- Si tu remplaces la référence de 3★ à 5★ :



Ce qui CHANGE :



La constante (l'intercept) : car elle représente le risque de l'avis de base (et un 5★ ne court pas le même risque de base qu'un 3★).

Les coefficients des autres étoiles (1★, 2★, 4★) : car comparer un 1★ à un 5★ ne donne évidemment pas le même écart que comparer un 1★ à un 3★.



Ce qui NE CHANGE PAS :



Les coefficients de Local Guide, du secteur, de la taille du texte, etc. Dans le modèle de 07\_regression\_panel.py, il n'y a pas de termes d'interaction (pas de variable croisée étoiles × local guide). Les effets sont purement additifs dans le logit : l'effet propre de Local Guide est donc totalement indépendant du choix de la note de référence.



les prénoms: sur tout 03B je crois donc Europe aussi. le graphique a boule par date : bah pk il a pas compris ?







Pic d'avis : 

Avis du jour : on compte les avis reçus par la fiche le jour où l'avis a été publié, l'avis lui-même compris. Le comptage se fait sur toute la base reviews, une ligne par avis.

Rythme habituel : on prend les avis reçus par la fiche sur les 365 jours avant le 11 août, et on divise par 365. Cela donne une moyenne d'avis par jour.

Rapport : avis du jour ÷ rythme habituel.

Variable du modèle : log(1 + rapport). C'est une valeur continue, sans aucun seuil : un avis n'est jamais classé « dans un pic » ou « hors pic ».

Le log(1 + rapport) entre tel quel dans la régression, comme une variable continue. Le modèle lui attribue un seul chiffre : de combien le risque est multiplié à chaque fois que log(1 + rapport) augmente de 1.



Augmenter le log de 1 revient à multiplier (1 + rapport) par 2,7 



Pour États-Unis et Europe sans les enseignes, le modèle donne ×0,90 par cran. Un avis publié un jour où la fiche reçoit 19 fois son rythme habituel (3 crans) a donc un risque de 0,90³ ≈ ×0,73, comparé à un avis publié un jour calme (rapport proche de 0), à caractéristiques égales. La fourchette (0,78 – 1,04) contient ×1 : cet effet n'est pas établi.







##### ***Ce qu'il a bien vu, et sur quoi je suis d'accord***

Ne garder que les 4 et 5 étoiles. On retire les suppressions sans doute demandées par le propriétaire, tout en gardant 78 % des suppressions (1 384 sur 1 770, sans les enseignes). Dans ce périmètre, la note n'est plus qu'un contrôle 4 contre 5 étoiles.

Exclure les petites fiches du calcul du pic. Une moyenne de 1 avis par jour ne permet pas de détecter un pic. Il faut un seuil minimal d'activité.

Le flux plutôt que le stock. On l'a déjà : 4,7 % des avis publiés pendant le relevé ont disparu en 12 jours. Il reste à le détailler par secteur.

Le graphique du pic au 7ᵉ jour plutôt que la courbe de survie, et des titres de graphiques qui affirment quelque chose.



##### ***Ce que j'ajouterais***

Mesurer le prénom. Pour Axel, c'est « 90 % de l'étude », et aujourd'hui ce n'est pas mesuré : on l'a seulement vu en lisant des groupes de textes. Il faut une caractéristique « l'avis cite un prénom », dans la régression sur les 4 et 5 étoiles, d'abord aux États-Unis avec une liste de prénoms, puis en Europe.

Lui montrer les jumeaux. C'est notre mesure la plus proche des avis payés :

même texte par plusieurs auteurs sur une fiche : ×4,0 ;

même auteur sur plusieurs fiches : ×6,7.

Sa demande sur la part d'avis génériques par fiche, comparée au taux de suppression de la fiche. C'est faisable avec les groupes de textes déjà calculés, sans refaire d'embeddings. Les fiches touchées sont peu nombreuses, donc le résultat sera fragile.

Refaire la régression sur les 4 et 5 étoiles, avec le pic redéfini et les secteurs comparés à l'ensemble.

Étendre le graphique du pic à 30 jours d'âge, en utilisant tous les avis et pas seulement ceux publiés pendant le relevé.

