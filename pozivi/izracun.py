def izracunaj_skupno_ceno(
        osebe,
        dnevi,
        prevoz,
        prehrana,
        lokalni_prevoz,
        aktivnosti,
        prenocisce):

    cena = (
        osebe * (
            prevoz +
            dnevi * prehrana +
            dnevi * lokalni_prevoz +
            aktivnosti
        )
        +
        dnevi * prenocisce
    )

    return cena