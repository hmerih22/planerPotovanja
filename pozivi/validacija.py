def preveri_vnos(
        proracun,
        dnevi,
        osebe):

    napake = []

    if proracun <= 0:
        napake.append(
            "Proračun mora biti večji od 0."
        )

    if dnevi <= 0:
        napake.append(
            "Število dni mora biti večje od 0."
        )

    if osebe <= 0:
        napake.append(
            "Število oseb mora biti večje od 0."
        )

    return napake