import streamlit as stl

import pandas as pd

import plotly.express as px

stl.set_page_config(
    page_title="Dashboard Titanic",
    page_icon="🚢",
    layout="wide"
)

def load_data():
    df=pd.read_csv("titanic_dataset.csv")

    df["Sex"]=df["Sex"].map({"male":"Homme","female":"Femme"})

    df["Survived"]=df["Survived"].map({0:"Décédé",1:"Survivant"})

    df["Pclass"]=df["Pclass"].map({1:"1ère",2:"2ième",3:"3ième"})

    df["Embarked"]=df["Embarked"].map({"C":"Cherboug","Q":"Queenstown","S":"SouthHampton"})

    return df

df= load_data()



with stl.sidebar:
    stl.title("Filtres")

    classes=stl.multiselect(
        "Pclass",options=["1ère","2ième","3ième"],
        default=["1ère","2ième","3ième"]
    )

    sexes=stl.multiselect(
        "Sex",options=["Homme","Femme"],
        default=["Homme","Femme"]
    )

    ports=stl.multiselect(
        "Port d'embarquement",
        options=["Cherboug","Queenstown","SouthHampton"],
        default=["Cherboug","Queenstown","SouthHampton"]
    )

    age_min,age_max = stl.slider(
        "Tranche d'age",0,80,(0,80)
    )

    condition=(
        df["Pclass"].isin(classes) & 
        df["Sex"].isin(sexes) &
        df["Embarked"].isin(ports) &
        df["Age"].between(age_min,age_max)
    )

df_filtre=df[condition]

stl.dataframe(df_filtre)

stl.title("🚢Titanic - Tableau de bord des passagers")
stl.caption("Explorez les passages du Titanic : qui etaient-ils, et qui a survécu")

# question 

# taux de survivant
taux_survie=(len(df_filtre[df_filtre["Survived"]=="Survivant"])/len(df_filtre)) * 100
taux_survie_total=(len(df[df["Survived"]=="Survivant"])/len(df)) * 100
# stl.write(f"{taux_survie} %")

# l'age moyen 
age_moyen=df_filtre["Age"].mean()
# stl.write(age_moyen)

# tarif moyen 
tarif_moyen=df_filtre["Fare"].mean()
# stl.write(tarif_moyen)

c1,c2,c3,c4,c5=stl.columns(5)

#nombre de passagerss

c1.metric('Nombre de passagers',f'{len(df_filtre)}')

c2.metric("Âge moyen" , f"{df['Age'].mean() : .1f} ans")

c3.metric("Tarif moyen" , f"{df_filtre['Fare'].mean() : .2f} USD")

c4.metric("Taux de survie",f"{taux_survie:.2f}%",delta=f"{(taux_survie - taux_survie_total):.2f}%")

c5.metric("Âge moyen de personnes survivants" , f"{df[df["Survived"]=="Survivant"]['Age'].mean() : .1f} ans")

onglet_survie , onglet_demo ,onglet_donnee = stl.tabs(
    ["Survie" , "Démographique" , "Données"]
)

with onglet_survie :
    g1 ,g2 ,g3 = stl.columns(3)
    #g1 = taux de survivant par sexe
    df_temp = df_filtre.copy()
    df_temp["survie"] = df_temp["Survived"]=="Survivant"

    taux_sexe = df_temp.groupby("Sex",as_index=False)["survie"].mean()

    fig = px.bar(
        taux_sexe,
        x="Sex",
        y="survie",
        text_auto=".0%",
        title="Répartition par sexe"
    )

    g1.plotly_chart(fig)

    # g2 -> taux de survivant par classe (Pclass)

    taux_class = df_temp.groupby("Pclass",as_index=False)["survie"].mean()

    fig2 = px.bar(
        taux_class,
        x="Pclass",
        y="survie",
        text_auto=".0%",
        title="Répartition par classe"
    )

    g2.plotly_chart(fig2)

    taux_class_sexe = df_temp.groupby(["Pclass" , "Sex"] , as_index=False)["survie"].mean()

    fig3 = px.bar(
        taux_class_sexe,
        x="Pclass",
        y="survie",
        text_auto=".0%",
        title="Répartition par classe et par sexe",
        color="Sex",
        barmode="group"
    )

    g3.plotly_chart(fig3)
