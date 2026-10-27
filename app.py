import streamlit as stl

import pandas as pd

import plotly.express as px

stl.set_page_config(page_title="Dashboard Titanic", page_icon="🚢", layout="wide")

BLEU = "#2a78d6"
AQUA = "#1baf7a"
GRIS = "#898781"

COULEURS_SEXE = {"Homme": BLEU, "Femme": AQUA}
COULEURS_FAMILLE = {"Seul": GRIS, "Petite famille": AQUA, "Grande famille": BLEU}

ORDRE = {
    "Pclass": ["1ère", "2ème", "3ème"],
    "Sex": ["Homme", "Femme"],
    "Embarked": ["Cherbourg", "Queenstown", "Southampton", "Inconnu"],
    "type_famille": ["Seul", "Petite famille", "Grande famille"],
    "Survived": ["Survivant", "Décédé"],
    "titre": ["Mr", "Mrs", "Miss", "Master", "Autre"],
    "tranche_age": ["Enfant", "Ado", "Jeune adulte", "Adulte", "Vieux"],
}

LIBELLES = {
    "Pclass": "Classe",
    "Sex": "Sexe",
    "type_famille": "Type de famille",
    "taux": "Taux de survie (%)",
    "Age": "Âge (années)",
    "Survived": "Statut",
    "Embarked": "Port d'embarquement",
    "tranche_age": "Tranche d'âge",
    "effectif": "Nombre de passagers",
}


@stl.cache_data
def load_data():
    df = pd.read_csv("titanic_dataset.csv")

    df["Sex"] = df["Sex"].map({"male": "Homme", "female": "Femme"})

    df["Survived"] = df["Survived"].map({0: "Décédé", 1: "Survivant"})

    df["Pclass"] = df["Pclass"].map({1: "1ère", 2: "2ème", 3: "3ème"})

    df["Embarked"] = (
        df["Embarked"]
        .map({"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"})
        .fillna("Inconnu")
    )

    df["taille_famille"] = df["SibSp"] + df["Parch"] + 1
    df["type_famille"] = pd.cut(
        df["taille_famille"],
        bins=[0, 1, 4, df["taille_famille"].max()],
        labels=ORDRE["type_famille"],
    ).astype(str)

    df["titre"] = df["Name"].str.extract(r",\s*([^.]+)\.")[0].str.strip()
    df["titre"] = df["titre"].replace({"Mlle": "Miss", "Ms": "Miss", "Mme": "Mrs"})
    df.loc[~df["titre"].isin(["Mr", "Mrs", "Miss", "Master"]), "titre"] = "Autre"

    df["age_impute"] = df["Age"].isna()
    df["Age"] = df["Age"].fillna(df.groupby("titre")["Age"].transform("median"))

    # Tranches d'âge du cours (0-12, 12-18, 18-35, 35-60, 60+)
    df["tranche_age"] = pd.cut(
        df["Age"],
        bins=[0, 12, 18, 35, 60, 100],
        labels=ORDRE["tranche_age"],
    ).astype(str)

    return df


def taux_par(data, colonnes):
    resultat = (
        data.assign(survie=data["Survived"] == "Survivant")
        .groupby(colonnes, as_index=False)
        .agg(
            taux=("survie", "mean"),
            survivants=("survie", "sum"),
            effectif=("survie", "size"),
        )
    )
    return resultat


def taux_global(data):
    if len(data) == 0:
        return None
    return (data["Survived"] == "Survivant").mean()


def graphique_taux(data, x, titre, color=None):
    colonnes = [x] if color is None else [x, color]
    fig = px.bar(
        taux_par(data, colonnes),
        x=x,
        y="taux",
        color=color,
        barmode="group",
        text_auto=".0%",
        title=titre,
        category_orders=ORDRE,
        color_discrete_map={**COULEURS_SEXE, **COULEURS_FAMILLE},
        color_discrete_sequence=[BLEU],
        labels=LIBELLES,
        hover_data=["survivants", "effectif"],
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    return fig


def graphique_effectif(data, x, titre):
    effectifs = data[x].value_counts().reset_index(name="effectif")
    fig = px.bar(
        effectifs,
        x=x,
        y="effectif",
        text_auto=True,
        title=titre,
        category_orders=ORDRE,
        color_discrete_sequence=[BLEU],
        labels=LIBELLES,
    )
    return fig


df = load_data()


with stl.sidebar:
    stl.title("Filtres")

    classes = stl.multiselect(
        "Classe", options=ORDRE["Pclass"], default=ORDRE["Pclass"]
    )

    sexes = stl.multiselect("Sexe", options=ORDRE["Sex"], default=ORDRE["Sex"])

    ports = stl.multiselect(
        "Port d'embarquement", options=ORDRE["Embarked"], default=ORDRE["Embarked"]
    )

    familles = stl.multiselect(
        "Type de famille", options=ORDRE["type_famille"], default=ORDRE["type_famille"]
    )

    age_min, age_max = stl.slider("Tranche d'âge", 0, 80, (0, 80))

    condition = (
        df["Pclass"].isin(classes)
        & df["Sex"].isin(sexes)
        & df["Embarked"].isin(ports)
        & df["type_famille"].isin(familles)
        & df["Age"].between(age_min, age_max)
    )

df_filtre = df[condition]

stl.title("🚢 Titanic - Tableau de bord des passagers")
stl.caption(
    "Explorez les passagers du Titanic : qui étaient-ils, et qui a survécu ? "
    f"Source : titanic_dataset.csv ({len(df)} passagers)."
)

if df_filtre.empty:
    stl.warning(
        "Aucun passager ne correspond aux filtres choisis. "
        "Cochez au moins une modalité dans chaque filtre de la barre latérale."
    )
    stl.stop()

taux_survie = taux_global(df_filtre) * 100
taux_survie_total = taux_global(df) * 100

c1, c2, c3, c4, c5 = stl.columns(5)

c1.metric("Nombre de passagers", f"{len(df_filtre)}")

c2.metric("Âge moyen", f"{df_filtre['Age'].mean():.1f} ans")

c3.metric("Tarif moyen", f"{df_filtre['Fare'].mean():.2f} USD")

c4.metric(
    "Taux de survie",
    f"{taux_survie:.1f} %",
    delta=f"{taux_survie - taux_survie_total:.1f} pts vs base",
)

c5.metric(
    "Âge moyen des survivants",
    f"{df_filtre[df_filtre['Survived'] == 'Survivant']['Age'].mean():.1f} ans",
)

onglet_survie, onglet_demo, onglet_familles, onglet_donnee = stl.tabs(
    ["Survie", "Démographie", "Familles", "Données"]
)

with onglet_survie:
    g1, g2, g3 = stl.columns(3)

    g1.plotly_chart(graphique_taux(df_filtre, "Sex", "Taux de survie par sexe (%)"))

    g2.plotly_chart(
        graphique_taux(df_filtre, "Pclass", "Taux de survie par classe (%)")
    )

    g3.plotly_chart(
        graphique_taux(
            df_filtre, "Pclass", "Taux de survie par classe et sexe (%)", color="Sex"
        )
    )

with onglet_demo:
    # Même découpage que le fichier du cours : sexe, port, puis tranches d'âge
    d1, d2 = stl.columns(2)

    d1.plotly_chart(
        graphique_effectif(df_filtre, "Sex", "Nombre de passagers par sexe")
    )

    d2.plotly_chart(
        graphique_taux(df_filtre, "Sex", "Taux de survie par sexe (%)"),
        key="demo_taux_sexe",
    )

    d3, d4 = stl.columns(2)

    d3.plotly_chart(
        graphique_effectif(
            df_filtre, "Embarked", "Nombre de passagers par port d'embarquement"
        )
    )

    d4.plotly_chart(
        graphique_taux(
            df_filtre, "Embarked", "Taux de survie par port d'embarquement (%)"
        )
    )

    # Part de chaque sexe parmi les survivants de chaque tranche d'âge
    df_survivants = df_filtre[df_filtre["Survived"] == "Survivant"]
    repartition = (
        df_survivants.groupby(["tranche_age", "Sex"]).size().reset_index(name="Nombre")
    )
    total_par_tranche = repartition.groupby("tranche_age")["Nombre"].transform("sum")
    repartition["Pourcentage"] = repartition["Nombre"] / total_par_tranche * 100

    fig_age = px.bar(
        repartition,
        x="tranche_age",
        y="Pourcentage",
        color="Sex",
        barmode="stack",
        text="Pourcentage",
        title="Répartition des survivants par sexe dans chaque tranche d'âge (%)",
        category_orders=ORDRE,
        color_discrete_map=COULEURS_SEXE,
        labels={**LIBELLES, "Pourcentage": "Part des survivants (%)"},
        hover_data=["Nombre"],
    )
    fig_age.update_traces(texttemplate="%{text:.1f} %", textposition="inside")
    fig_age.update_yaxes(range=[0, 100])
    stl.plotly_chart(fig_age)

with onglet_donnee:
    stl.dataframe(df_filtre)
    stl.download_button(
        "Télécharger les données filtrées (CSV)",
        df_filtre.to_csv(index=False).encode("utf-8"),
        file_name="titanic_filtre.csv",
        mime="text/csv",
    )

with onglet_familles:
    stl.subheader("Voyager en famille augmentait-il les chances de survie ?")

    # 2.5 Indicateurs : écarts par rapport à l'ensemble de la base
    seuls = df_filtre[df_filtre["type_famille"] == "Seul"]
    part_seuls = len(seuls) / len(df_filtre) * 100
    part_seuls_base = (df["type_famille"] == "Seul").mean() * 100

    grandes = df_filtre[df_filtre["type_famille"] == "Grande famille"]
    taux_grandes = taux_global(grandes)

    k1, k2 = stl.columns(2)
    k1.metric(
        "Passagers voyageant seuls",
        f"{len(seuls)} ({part_seuls:.1f} %)",
        delta=f"{part_seuls - part_seuls_base:.1f} pts de part vs base ({part_seuls_base:.1f} %)",
        delta_color="off",
    )
    if taux_grandes is None:
        k2.metric(
            "Taux de survie des grandes familles",
            "—",
            help="Aucune grande famille dans la sélection.",
        )
    else:
        k2.metric(
            "Taux de survie des grandes familles",
            f"{taux_grandes * 100:.1f} % ({len(grandes)} passagers)",
            delta=f"{taux_grandes * 100 - taux_survie_total:.1f} pts vs base ({taux_survie_total:.1f} %)",
        )

    # 2.1 et 2.2 Graphiques
    f1, f2 = stl.columns(2)

    f1.plotly_chart(
        graphique_taux(
            df_filtre, "type_famille", "Taux de survie par type de famille (%)"
        )
    )

    f2.plotly_chart(
        graphique_taux(
            df_filtre,
            "type_famille",
            "Taux de survie par type de famille et sexe (%)",
            color="Sex",
        )
    )

    f3, f4 = stl.columns(2)

    f3.plotly_chart(
        graphique_taux(
            df_filtre,
            "Pclass",
            "Taux de survie par classe et type de famille (%)",
            color="type_famille",
        )
    )

    croise = pd.crosstab(
        df_filtre["type_famille"],
        df_filtre["Pclass"],
        margins=True,
        margins_name="Total",
    )
    lignes = [t for t in ORDRE["type_famille"] if t in croise.index] + ["Total"]
    colonnes = [c for c in ORDRE["Pclass"] if c in croise.columns] + ["Total"]
    croise = croise.loc[lignes, colonnes]
    croise.index.name = "Type de famille"
    croise.columns.name = "Classe"

    f4.markdown("**Nombre de passagers par type de famille et classe**")
    f4.dataframe(croise)

    t_famille = taux_par(df, ["type_famille"]).set_index("type_famille")
    t_sexe_famille = taux_par(df, ["Sex", "type_famille"]).set_index(
        ["Sex", "type_famille"]
    )
    t_classe_famille = taux_par(df, ["Pclass", "type_famille"]).set_index(
        ["Pclass", "type_famille"]
    )
    croise_base = pd.crosstab(df["type_famille"], df["Pclass"])

    def cite(ligne):
        return f"{ligne['taux'] * 100:.0f} % ({int(ligne['survivants'])} sur {int(ligne['effectif'])})"

    nb_grandes = int(t_famille.loc["Grande famille", "effectif"])
    grandes_3e = int(croise_base.loc["Grande famille", "3ème"])

    stl.markdown("#### Interprétation")
    stl.caption(
        "Chiffres calculés sur l'ensemble des 891 passagers (graphiques sans filtre)."
    )
    stl.markdown(f"""
Voyager **en petite famille** (2 à 4 personnes) est associé à la meilleure survie : {cite(t_famille.loc["Petite famille"])},
contre {cite(t_famille.loc["Seul"])} pour les passagers seuls et seulement {cite(t_famille.loc["Grande famille"])} pour les grandes familles.
L'effet n'est donc pas « plus de famille = plus de chances » : la relation monte puis s'effondre au-delà de 4 personnes.
Par sexe, le gain concerne surtout les hommes : {cite(t_sexe_famille.loc[("Homme", "Petite famille")])} en petite famille contre {cite(t_sexe_famille.loc[("Homme", "Seul")])} seuls,
alors que les femmes survivent presque autant seules, {cite(t_sexe_famille.loc[("Femme", "Seul")])}, qu'en petite famille, {cite(t_sexe_famille.loc[("Femme", "Petite famille")])}.
**Explication concurrente, la classe :** {grandes_3e} des {nb_grandes} passagers en grande famille ({grandes_3e / nb_grandes * 100:.0f} %) voyageaient en 3e classe, la classe la moins bien lotie.
À classe égale, l'effet famille ne disparaît pas : en 3e classe, les petites familles survivent à {cite(t_classe_famille.loc[("3ème", "Petite famille")])}
contre {cite(t_classe_famille.loc[("3ème", "Seul")])} pour les seuls et {cite(t_classe_famille.loc[("3ème", "Grande famille")])} pour les grandes familles.
**Conclusion :** voyager en petite famille augmentait les chances de survie ; la très faible survie des grandes familles s'explique en partie par la 3e classe, mais reste nette même à l'intérieur de celle-ci.
""")