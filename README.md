# Winners Portfolio Management

Projet de gestion de portefeuille construisant deux portefeuilles de 25 actifs chacun, **Serenity** (profil prudent) et **Velocity** (profil dynamique). Les actifs sont sélectionnés par un screener, puis pondérés selon la théorie moderne du portefeuille de Markowitz en maximisant le ratio de Sharpe. Les résultats sont présentés dans un site web statique, avec une page d'analyse pour chaque graphe.

Site : https://Ynk10.github.io/winners-portfolio-management/

## Résultats

Période d'étude : 30 octobre 2023 au 29 octobre 2026. Taux sans risque : 4 %. Référence : S&P 500 (rendement annualisé de 23,01 %).

| Indicateur | Serenity | Velocity |
|---|---|---|
| Rendement annualisé | 22,56 % | 40,06 % |
| Volatilité annualisée | 8,34 % | 13,32 % |
| Ratio de Sharpe | 2,23 | 2,71 |
| Bêta (vs S&P 500) | 0,14 | 0,59 |
| Alpha de Jensen | 15,97 % | 24,92 % |

Ces indicateurs sont calculés sur la période d'optimisation (voir Limites).

## Méthode

1. **Sélection des actifs.** Un screener filtre l'univers d'investissement selon la qualité, la liquidité et la performance.
2. **Optimisation.** 10 000 portefeuilles aléatoires sont simulés pour visualiser la frontière rendement-risque. Le portefeuille retenu maximise le ratio de Sharpe.
3. **Analyse.** Chaque portefeuille dispose de six pages d'analyse : prix en base 100, rendements journaliers, distribution des rendements, allocation optimale, portefeuilles simulés (droite de marché des capitaux) et contribution à la variance. Une page Actualités regroupe les articles récents sur les 25 actifs.

## Structure du dépôt

```
index.html              Page d'accueil
1.html, 2.html          Tableaux de bord Serenity et Velocity
analytics/1, 2/         Pages d'analyse et actualités de chaque portefeuille
css/                    Feuilles de style
img/1, 2/               Graphes Plotly générés(HTML), CSV, poids et risques,jauges comprises
par84.py                Paramètres communs des graphes
marko.py                Calcul et génération des graphes(Chaque dossier avec son marko)
```

## Exécution locale

Prérequis : Python 3.10 ou supérieur.

```bash
pip install yfinance pandas numpy scipy plotly
python marko.py                 # régénère les graphes du portefeuille choisi
python analytics/1/news.py      # met à jour les actualités de Serenity
python analytics/2/news.py      # met à jour les actualités de Velocity
```

Le site est statique : il suffit d'ouvrir `index.html` dans un navigateur.

## Limites

- Les poids sont optimisés et mesurés sur la même période : les ratios de Sharpe sont donc optimistes par construction.
- Les estimations reposent sur environ trois ans de données, très favorables aux valeurs de semi-conducteurs pour Velocity.
- Les prix sont exprimés en devise locale, sans conversion.
- Le modèle de Markowitz résume le risque par la variance et ne tient pas compte de l'épaisseur des queues de distribution observée sur les rendements.
- Les jours fériés propres à chaque place boursière créent des valeurs manquantes comblées, ce qui peut sous-estimer la volatilité de certains actifs, notamment japonais.

## Perspectives

- **Value at Risk et Expected Shortfall** sur un capital de 1 milliard de dollars par portefeuille, avec trois méthodes (paramétrique, historique, Cornish-Fisher), et deux pages d'analyse supplémentaires.
- **Modélisation GARCH** de la volatilité conditionnelle, pour tenir compte du regroupement des épisodes de forte volatilité.
- **Validation hors échantillon** : backtesting en fenêtre glissante des poids et de la VaR.
- **Estimation plus robuste** de la covariance (shrinkage de Ledoit-Wolf) et des rendements attendus (Black-Litterman).
- **Contraintes de portefeuille** : plafonds par actif, par secteur et par pays, rééquilibrage périodique avec coûts de transaction.
- **Conversion des prix** dans une devise commune.
- **Automatisation** de la page Actualités par une tâche planifiée (GitHub Actions).

## Analyste

Yannick TCHALLA

## Avertissement

Projet pédagogique. Il ne constitue pas un conseil en investissement. Les performances passées ne préjugent pas des performances futures.