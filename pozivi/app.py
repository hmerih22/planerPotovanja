from flask import Flask, render_template, request
from baza import pridobi_destinacije, ustvari_tabelo
from izracun import izracunaj_skupno_ceno

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/rezultati", methods=["POST"])
def rezultati():

    proracun = float(request.form["proracun"])
    dnevi = int(request.form["dnevi"])
    osebe = int(request.form["osebe"])

    destinacije = pridobi_destinacije()

    rezultati = []

    for d in destinacije:

        cena = izracunaj_skupno_ceno(
            osebe,
            dnevi,
            d["prevoz"],
            d["prehrana"],
            d["lokalni_prevoz"],
            d["aktivnosti"],
            d["prenocisce"]
        )

        if cena <= proracun:
            rezultati.append({
                "ime": d["ime"],
                "cena": round(cena, 2),
                "razlika": round(proracun - cena, 2),
                "razlaga": "Destinacija je znotraj vašega proračuna in je med najbližjimi izbranemu znesku."
            })

    rezultati.sort(key=lambda x: x["razlika"])

    top3 = rezultati[:3]

    return render_template(
        "rezultati.html",
        destinacije=top3
    )


if __name__ == "__main__":
    ustvari_tabelo()
    app.run(debug=True)