# -*- coding: utf-8 -*-
"""
COINTECA S.A.S. - Módulo de Ingeniería
simco_matriz.py - Matriz maestra de conexiones SIMCO (Materiales y Mano de Obra Contractual)
"""

import json
from decimal import Decimal
from django.db.models import Sum
from core.models import Proyecto, Material, MaterialRequeridoProyecto, ApoyoMaterial, ItemManoObra

REGLAS_SIMCO_RAW = """{
  "518": {
    "material": "SERV SUM/INST ABRAZ SIN SDA 10 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "519": {
    "material": "SERV SUM/INST ABRAZ SIN SDA 4 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "520": {
    "material": "SERV SUM/INST ABRAZ SIN SDA 5 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "521": {
    "material": "SERV SUM/INST ABRAZ SIN SDA 6 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "522": {
    "material": "SERV SUM/INST ABRAZ SIN SDA 7 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "523": {
    "material": "SERV SUM/INST ABRAZ SIN SDA 8 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "524": {
    "material": "SERV SUM/INST ABRAZ TIPO CORONA 10 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      },
      {
        "id_mo": "248",
        "mano_obra": "SERV INST CORONA DE SEGURIDAD",
        "valor": 53451
      }
    ]
  },
  "525": {
    "material": "SERV SUM/INST ABRAZ TIPO CORONA 6 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      },
      {
        "id_mo": "248",
        "mano_obra": "SERV INST CORONA DE SEGURIDAD",
        "valor": 53451
      }
    ]
  },
  "526": {
    "material": "SERV SUM/INST ABRAZ TIPO CORONA 7 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      },
      {
        "id_mo": "248",
        "mano_obra": "SERV INST CORONA DE SEGURIDAD",
        "valor": 53451
      }
    ]
  },
  "527": {
    "material": "SERV SUM/INST ABRAZ UNA SDA 10 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "528": {
    "material": "SERV SUM/INST ABRAZ UNA SDA 4 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "529": {
    "material": "SERV SUM/INST ABRAZ UNA SDA 5 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "530": {
    "material": "SERV SUM/INST ABRAZ UNA SDA 6 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "531": {
    "material": "SERV SUM/INST ABRAZ UNA SDA 7 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "532": {
    "material": "SERV SUM/INST ABRAZ UNA SDA 8 PULG",
    "manos_de_obra": [
      {
        "id_mo": "291",
        "mano_obra": "SERV TRANSP COLLARIN",
        "valor": 390
      }
    ]
  },
  "536": {
    "material": "SERV SUM/INST ALAMBRE CU THHN 14VERDE",
    "manos_de_obra": [
      {
        "id_mo": "242",
        "mano_obra": "SERV INST CABLE SEC 14 EN DUCT ADOS",
        "valor": 1091
      },
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      }
    ]
  },
  "537": {
    "material": "SERV SUM/INST ANGULAR EN V 18X48 PULG",
    "manos_de_obra": [
      {
        "id_mo": "296",
        "mano_obra": "SERV TRANSP DIAGONALES",
        "valor": 3980
      }
    ]
  },
  "575": {
    "material": "SERV SUM/INST BRAZO 1 1-2X6 C12 PERF",
    "manos_de_obra": [
      {
        "id_mo": "293",
        "mano_obra": "SERV TRANSP BRAZOS 2 1-2 PULG HASTA 6M",
        "valor": 0
      }
    ]
  },
  "579": {
    "material": "SERV SUM/INST BRAZO GALV 1 1-2X1.5MC12 tipo L",
    "manos_de_obra": [
      {
        "id_mo": "292",
        "mano_obra": "SERV TRANSP BRAZOS 1 1-2 PULG HASTA 3M",
        "valor": 4098
      }
    ]
  },
  "577": {
    "material": "SERV SUM/INST BRAZO GALV 1 1-2X2M C12",
    "manos_de_obra": [
      {
        "id_mo": "292",
        "mano_obra": "SERV TRANSP BRAZOS 1 1-2 PULG HASTA 3M",
        "valor": 4098
      }
    ]
  },
  "578": {
    "material": "SERV SUM/INST BRAZO GALV 1 1-2X3M C12",
    "manos_de_obra": [
      {
        "id_mo": "292",
        "mano_obra": "SERV TRANSP BRAZOS 1 1-2 PULG HASTA 3M",
        "valor": 4098
      }
    ]
  },
  "576": {
    "material": "SERV SUM/INST BRAZO GALVÂ 2 1-2X6M C12",
    "manos_de_obra": [
      {
        "id_mo": "293",
        "mano_obra": "SERV TRANSP BRAZOS 2 1-2 PULG HASTA 6M",
        "valor": 0
      }
    ]
  },
  "580": {
    "material": "SERV SUM/INST BRAZP SENCILLO 2M NEGRO",
    "manos_de_obra": [
      {
        "id_mo": "292",
        "mano_obra": "SERV TRANSP BRAZOS 1 1-2 PULG HASTA 3M",
        "valor": 4098
      }
    ]
  },
  "584": {
    "material": "SERV SUM/INST CABLE AL AA-8000 1-0 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "245",
        "mano_obra": "SERV INST CABLE SEC 4 A 2-0 AEREO",
        "valor": 0
      }
    ]
  },
  "585": {
    "material": "SERV SUM/INST CABLE AL AA-8000 4 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "245",
        "mano_obra": "SERV INST CABLE SEC 4 A 2-0 AEREO",
        "valor": 0
      }
    ]
  },
  "586": {
    "material": "SERV SUM/INST CABLE AL AA-8000 6 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "245",
        "mano_obra": "SERV INST CABLE SEC 4 A 2-0 AEREO",
        "valor": 0
      }
    ]
  },
  "581": {
    "material": "SERV SUM/INST CABLE AL PVC THHN 1-0 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "246",
        "mano_obra": "SERV INST CABLE SEC 4 A 2-0 SUBT",
        "valor": 547
      }
    ]
  },
  "582": {
    "material": "SERV SUM/INST CABLE AL PVC THHN 4 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "246",
        "mano_obra": "SERV INST CABLE SEC 4 A 2-0 SUBT",
        "valor": 547
      }
    ]
  },
  "583": {
    "material": "SERV SUM/INST CABLE AL PVC THHN 6 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "246",
        "mano_obra": "SERV INST CABLE SEC 4 A 2-0 SUBT",
        "valor": 547
      }
    ]
  },
  "588": {
    "material": "SERV SUM/INST CABLE AL TPX 2X2 1X2 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "324",
        "mano_obra": "SERV TRANSP/INST CABLE TPX 2X2+1X2 AWG",
        "valor": 0
      }
    ]
  },
  "589": {
    "material": "SERV SUM/INST CABLE AL TPX 2X4 1X4 AWG",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "323",
        "mano_obra": "SERV TRANSP/INST CABLE TPX 2X4+1X4 AWG",
        "valor": 3258
      }
    ]
  },
  "590": {
    "material": "SERV SUM/INST CABLE ENCAUCHE 3X14 PVC",
    "manos_de_obra": [
      {
        "id_mo": "294",
        "mano_obra": "SERV TRANSP CABLE",
        "valor": 512
      },
      {
        "id_mo": "241",
        "mano_obra": "SERV INST CABLE ENCAUCH EN TUB ADOS PTE",
        "valor": 2766
      }
    ]
  },
  "607": {
    "material": "SERV SUM/INST CONCERT INOX DIAM 45CMX6M",
    "manos_de_obra": [
      {
        "id_mo": "255",
        "mano_obra": "SERV INST DE CONCERTINA POR METRO",
        "valor": 0
      }
    ]
  },
  "622": {
    "material": "SERV SUM/INST CORAZA AME METALICA 3-4 P",
    "manos_de_obra": [
      {
        "id_mo": "247",
        "mano_obra": "SERV INST CORAZA AMER LT 1-2 3-4 Y 1P",
        "valor": 27290
      },
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      }
    ]
  },
  "623": {
    "material": "SERV SUM/INST CRUCE MET 3X3X1-4 PX2.4M",
    "manos_de_obra": [
      {
        "id_mo": "322",
        "mano_obra": "SERV VEST DE CRUCETAS CONJ. SECUNDARIO",
        "valor": 81764
      },
      {
        "id_mo": "295",
        "mano_obra": "SERV TRANSP CRUCETAS HASTA 3 MTS",
        "valor": 4133
      }
    ]
  },
  "631": {
    "material": "SERV SUM/INST EMP GEL GFCH 8-4-0A14-2-0",
    "manos_de_obra": [
      {
        "id_mo": "257",
        "mano_obra": "SERV INST DE CUBIERTA GEL CONECTORÂ GHFC",
        "valor": 10462
      }
    ]
  },
  "632": {
    "material": "SERV SUM/INST EMP GEL GHFC1 CONECT PPAL",
    "manos_de_obra": [
      {
        "id_mo": "257",
        "mano_obra": "SERV INST DE CUBIERTA GEL CONECTORÂ GHFC",
        "valor": 10462
      }
    ]
  },
  "633": {
    "material": "SERV SUM/INST EMP GEL GHFC2 CONECT PPAL",
    "manos_de_obra": [
      {
        "id_mo": "257",
        "mano_obra": "SERV INST DE CUBIERTA GEL CONECTORÂ GHFC",
        "valor": 10462
      }
    ]
  },
  "634": {
    "material": "SERV SUM/INST EMP GEL PPAL 4-2-0A14-6",
    "manos_de_obra": [
      {
        "id_mo": "257",
        "mano_obra": "SERV INST DE CUBIERTA GEL CONECTORÂ GHFC",
        "valor": 10462
      }
    ]
  },
  "643": {
    "material": "SERV SUM/INST KIT PTA TIERRA ACE INOX",
    "manos_de_obra": [
      {
        "id_mo": "266",
        "mano_obra": "SERV INST KIT SPT CINTA METALICA",
        "valor": 56079
      },
      {
        "id_mo": "319",
        "mano_obra": "SERV TRANSP VARI TIER Y-O KIT TIER ACERO",
        "valor": 1056
      }
    ]
  },
  "699": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 110W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "269",
        "mano_obra": "SERV INST LUMS EN CANASTA",
        "valor": 92692
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "700": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 120W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "269",
        "mano_obra": "SERV INST LUMS EN CANASTA",
        "valor": 92692
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "701": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 150W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "269",
        "mano_obra": "SERV INST LUMS EN CANASTA",
        "valor": 92692
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "702": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 190W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "269",
        "mano_obra": "SERV INST LUMS EN CANASTA",
        "valor": 92692
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "693": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 25W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "268",
        "mano_obra": "SERV INST LUMS EN CAMIONETA",
        "valor": 50750
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "694": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 40W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "268",
        "mano_obra": "SERV INST LUMS EN CAMIONETA",
        "valor": 50750
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "695": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 50W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "268",
        "mano_obra": "SERV INST LUMS EN CAMIONETA",
        "valor": 50750
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "696": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 60W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "268",
        "mano_obra": "SERV INST LUMS EN CAMIONETA",
        "valor": 50750
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "697": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 75W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "268",
        "mano_obra": "SERV INST LUMS EN CAMIONETA",
        "valor": 50750
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "698": {
    "material": "SERV SUM/INST LUM LED HORIZ CERR DE 95W",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "268",
        "mano_obra": "SERV INST LUMS EN CAMIONETA",
        "valor": 50750
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "707": {
    "material": "SERV SUM/INST LUMINARIA CURRENT TIPO FAROL 6OW",
    "manos_de_obra": [
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "268",
        "mano_obra": "SERV INST LUMS EN CAMIONETA",
        "valor": 50750
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "648": {
    "material": "SERV SUM/INST PERCHA GALV CAL 1 PUEST",
    "manos_de_obra": [
      {
        "id_mo": "320",
        "mano_obra": "SERV VEST CONJUNTO 1 O 2 PERCHAS",
        "valor": 26667
      },
      {
        "id_mo": "301",
        "mano_obra": "SERV TRANSP PERCHA CON AISLADOR",
        "valor": 588
      }
    ]
  },
  "649": {
    "material": "SERV SUM/INST PERCHA GALV CAL 10 2 PUEST",
    "manos_de_obra": [
      {
        "id_mo": "320",
        "mano_obra": "SERV VEST CONJUNTO 1 O 2 PERCHAS",
        "valor": 26667
      },
      {
        "id_mo": "301",
        "mano_obra": "SERV TRANSP PERCHA CON AISLADOR",
        "valor": 588
      }
    ]
  },
  "689": {
    "material": "SERV SUM/INST POST MET 10M ENTER 510 KGF",
    "manos_de_obra": [
      {
        "id_mo": "194",
        "mano_obra": "SERV APERT HUECO POST SECUND 8 A 10 MTS",
        "valor": 0
      },
      {
        "id_mo": "198",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 8A10M",
        "valor": 37598
      },
      {
        "id_mo": "234",
        "mano_obra": "SERV HINCADA DE POSTE FIBRA DE 10 A 12M",
        "valor": 46215
      },
      {
        "id_mo": "290",
        "mano_obra": "SERV TRANSP.POSTE.METALICO DE 4 A 12MT",
        "valor": 27839
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "690": {
    "material": "SERV SUM/INST POST MET 12M ENTER 510 KGF",
    "manos_de_obra": [
      {
        "id_mo": "193",
        "mano_obra": "SERV APERT HUECO POST PRIM 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "197",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 11A14M",
        "valor": 47859
      },
      {
        "id_mo": "234",
        "mano_obra": "SERV HINCADA DE POSTE FIBRA DE 10 A 12M",
        "valor": 46215
      },
      {
        "id_mo": "290",
        "mano_obra": "SERV TRANSP.POSTE.METALICO DE 4 A 12MT",
        "valor": 27839
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "691": {
    "material": "SERV SUM/INST POST MET 14M ENTER 510 KGF",
    "manos_de_obra": [
      {
        "id_mo": "193",
        "mano_obra": "SERV APERT HUECO POST PRIM 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "197",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 11A14M",
        "valor": 47859
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "688": {
    "material": "SERV SUM/INST POST MET 8M FLANCH 150 KGF",
    "manos_de_obra": [
      {
        "id_mo": "194",
        "mano_obra": "SERV APERT HUECO POST SECUND 8 A 10 MTS",
        "valor": 0
      },
      {
        "id_mo": "198",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 8A10M",
        "valor": 37598
      },
      {
        "id_mo": "235",
        "mano_obra": "SERV HINCADA DE POSTE FIBRA DE 8M",
        "valor": 0
      },
      {
        "id_mo": "290",
        "mano_obra": "SERV TRANSP.POSTE.METALICO DE 4 A 12MT",
        "valor": 27839
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "653": {
    "material": "SERV SUM/INST POSTE CONC 10MX510KG D.I",
    "manos_de_obra": [
      {
        "id_mo": "194",
        "mano_obra": "SERV APERT HUECO POST SECUND 8 A 10 MTS",
        "valor": 0
      },
      {
        "id_mo": "196",
        "mano_obra": "SERV APLOMADA POST CONC 8 A 10 MTS",
        "valor": 50897
      },
      {
        "id_mo": "237",
        "mano_obra": "SERV HINCADA DE POST CONC DE 8 A 12 MTS",
        "valor": 0
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "654": {
    "material": "SERV SUM/INST POSTE CONC 12MX510KG D.I",
    "manos_de_obra": [
      {
        "id_mo": "193",
        "mano_obra": "SERV APERT HUECO POST PRIM 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "195",
        "mano_obra": "SERV APLOMADA POST CONC 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "237",
        "mano_obra": "SERV HINCADA DE POST CONC DE 8 A 12 MTS",
        "valor": 0
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "655": {
    "material": "SERV SUM/INST POSTE CONC 14MX750KG D.I",
    "manos_de_obra": [
      {
        "id_mo": "193",
        "mano_obra": "SERV APERT HUECO POST PRIM 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "195",
        "mano_obra": "SERV APLOMADA POST CONC 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "236",
        "mano_obra": "SERV HINCADA DE POST CONC DE 14 MTS",
        "valor": 92866
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "656": {
    "material": "SERV SUM/INST POSTE CONC 8MX510KG D.I",
    "manos_de_obra": [
      {
        "id_mo": "194",
        "mano_obra": "SERV APERT HUECO POST SECUND 8 A 10 MTS",
        "valor": 0
      },
      {
        "id_mo": "196",
        "mano_obra": "SERV APLOMADA POST CONC 8 A 10 MTS",
        "valor": 50897
      },
      {
        "id_mo": "237",
        "mano_obra": "SERV HINCADA DE POST CONC DE 8 A 12 MTS",
        "valor": 0
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "661": {
    "material": "SERV SUM/INST POSTE FIBRA 8MX510 KG NEG",
    "manos_de_obra": [
      {
        "id_mo": "194",
        "mano_obra": "SERV APERT HUECO POST SECUND 8 A 10 MTS",
        "valor": 0
      },
      {
        "id_mo": "198",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 8A10M",
        "valor": 37598
      },
      {
        "id_mo": "235",
        "mano_obra": "SERV HINCADA DE POSTE FIBRA DE 8M",
        "valor": 0
      },
      {
        "id_mo": "290",
        "mano_obra": "SERV TRANSP.POSTE.METALICO DE 4 A 12MT",
        "valor": 27839
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "657": {
    "material": "SERV SUM/INST POSTE FIBRA V 10MX510 KG",
    "manos_de_obra": [
      {
        "id_mo": "194",
        "mano_obra": "SERV APERT HUECO POST SECUND 8 A 10 MTS",
        "valor": 0
      },
      {
        "id_mo": "198",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 8A10M",
        "valor": 37598
      },
      {
        "id_mo": "234",
        "mano_obra": "SERV HINCADA DE POSTE FIBRA DE 10 A 12M",
        "valor": 46215
      },
      {
        "id_mo": "290",
        "mano_obra": "SERV TRANSP.POSTE.METALICO DE 4 A 12MT",
        "valor": 27839
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "658": {
    "material": "SERV SUM/INST POSTE FIBRA V 12MX510 KG",
    "manos_de_obra": [
      {
        "id_mo": "193",
        "mano_obra": "SERV APERT HUECO POST PRIM 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "197",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 11A14M",
        "valor": 47859
      },
      {
        "id_mo": "234",
        "mano_obra": "SERV HINCADA DE POSTE FIBRA DE 10 A 12M",
        "valor": 46215
      },
      {
        "id_mo": "290",
        "mano_obra": "SERV TRANSP.POSTE.METALICO DE 4 A 12MT",
        "valor": 27839
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "659": {
    "material": "SERV SUM/INST POSTE FIBRA V 14MX510 KG",
    "manos_de_obra": [
      {
        "id_mo": "193",
        "mano_obra": "SERV APERT HUECO POST PRIM 11A14 MTS",
        "valor": 0
      },
      {
        "id_mo": "197",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 11A14M",
        "valor": 47859
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "662": {
    "material": "SERV SUM/INST POSTE FIBRA V 8MX510 KG",
    "manos_de_obra": [
      {
        "id_mo": "194",
        "mano_obra": "SERV APERT HUECO POST SECUND 8 A 10 MTS",
        "valor": 0
      },
      {
        "id_mo": "198",
        "mano_obra": "SERV APLOMADA POST MET Y-O FIBRA 8A10M",
        "valor": 37598
      },
      {
        "id_mo": "235",
        "mano_obra": "SERV HINCADA DE POSTE FIBRA DE 8M",
        "valor": 0
      },
      {
        "id_mo": "290",
        "mano_obra": "SERV TRANSP.POSTE.METALICO DE 4 A 12MT",
        "valor": 27839
      },
      {
        "id_mo": "202",
        "mano_obra": "SERV BOTADO DE ESCOMBROS",
        "valor": 29161
      }
    ]
  },
  "705": {
    "material": "SERV SUM/INST PROY LED CERRADO DE 140W",
    "manos_de_obra": [
      {
        "id_mo": "259",
        "mano_obra": "SERV INST DE REFLECTOR",
        "valor": 97543
      },
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "706": {
    "material": "SERV SUM/INST PROY LED CERRADO DE 190W",
    "manos_de_obra": [
      {
        "id_mo": "259",
        "mano_obra": "SERV INST DE REFLECTOR",
        "valor": 97543
      },
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "703": {
    "material": "SERV SUM/INST PROY LED CERRADO DE 50W",
    "manos_de_obra": [
      {
        "id_mo": "259",
        "mano_obra": "SERV INST DE REFLECTOR",
        "valor": 97543
      },
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "704": {
    "material": "SERV SUM/INST PROY LED CERRADO DE 90W",
    "manos_de_obra": [
      {
        "id_mo": "259",
        "mano_obra": "SERV INST DE REFLECTOR",
        "valor": 97543
      },
      {
        "id_mo": "287",
        "mano_obra": "SERV TRANSP LUMS PROYES",
        "valor": 5561
      },
      {
        "id_mo": "213",
        "mano_obra": "SERV CONEX A CABLE TIER (INST CONEC SPT)",
        "valor": 2026
      }
    ]
  },
  "670": {
    "material": "SERV SUM/INST TAPA PARA CAJA AP",
    "manos_de_obra": [
      {
        "id_mo": "300",
        "mano_obra": "SERV TRANSP TAPA PARA CAJA A.P.",
        "valor": 5103
      },
      {
        "id_mo": "280",
        "mano_obra": "SERV RECUPERACION TAPA PARA CAJA AP",
        "valor": 143666
      }
    ]
  },
  "673": {
    "material": "SERV SUM/INST TUBERIA CONDUFLEX 3-4 P",
    "manos_de_obra": [
      {
        "id_mo": "247",
        "mano_obra": "SERV INST CORAZA AMER LT 1-2 3-4 Y 1P",
        "valor": 27290
      },
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      }
    ]
  },
  "674": {
    "material": "SERV SUM/INST TUBO CONDUIT EMT 3-4 PULG",
    "manos_de_obra": [
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      },
      {
        "id_mo": "251",
        "mano_obra": "SERV INST DE BAJANTE SECUNDARIO",
        "valor": 85242
      }
    ]
  },
  "675": {
    "material": "SERV SUM/INST TUBO CONDUIT EMT 1 PULG",
    "manos_de_obra": [
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      },
      {
        "id_mo": "251",
        "mano_obra": "SERV INST DE BAJANTE SECUNDARIO",
        "valor": 85242
      }
    ]
  },
  "676": {
    "material": "SERV SUM/INST TUBO CONDUIT IMC 2 PULG",
    "manos_de_obra": [
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      },
      {
        "id_mo": "251",
        "mano_obra": "SERV INST DE BAJANTE SECUNDARIO",
        "valor": 85242
      }
    ]
  },
  "677": {
    "material": "SERV SUM/INST TUBO CONDUIT IMC 3-4 PULG",
    "manos_de_obra": [
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      },
      {
        "id_mo": "251",
        "mano_obra": "SERV INST DE BAJANTE SECUNDARIO",
        "valor": 85242
      }
    ]
  },
  "678": {
    "material": "SERV SUM/INST TUBO CONDUIT IMC 1-2 P",
    "manos_de_obra": [
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      },
      {
        "id_mo": "251",
        "mano_obra": "SERV INST DE BAJANTE SECUNDARIO",
        "valor": 85242
      }
    ]
  },
  "679": {
    "material": "SERV SUM/INST TUBO PVC CONDUIT 1-2PX3",
    "manos_de_obra": [
      {
        "id_mo": "231",
        "mano_obra": "SERV EXCAV ZONA BL INC INST 2 TUB Y RELL",
        "valor": 27346
      },
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      }
    ]
  },
  "680": {
    "material": "SERV SUM/INST TUBO PVC CONDUIT 2â€X3MTS",
    "manos_de_obra": [
      {
        "id_mo": "231",
        "mano_obra": "SERV EXCAV ZONA BL INC INST 2 TUB Y RELL",
        "valor": 27346
      },
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      }
    ]
  },
  "681": {
    "material": "SERV SUM/INST TUBO PVC CONDUIT 3-4P3M",
    "manos_de_obra": [
      {
        "id_mo": "231",
        "mano_obra": "SERV EXCAV ZONA BL INC INST 2 TUB Y RELL",
        "valor": 27346
      },
      {
        "id_mo": "318",
        "mano_obra": "SERV TRANSP TUBERIA HASTA 4 PULG",
        "valor": 2754
      }
    ]
  },
  "686": {
    "material": "SERV SUM/INST VARILLA COOPERW 5-8PX2.4M",
    "manos_de_obra": [
      {
        "id_mo": "249",
        "mano_obra": "SERV INST DE ATERRIZAJES SECUNDARIOS",
        "valor": 58894
      },
      {
        "id_mo": "319",
        "mano_obra": "SERV TRANSP VARI TIER Y-O KIT TIER ACERO",
        "valor": 1056
      }
    ]
  }
}"""

_REGLAS_CACHE = None

def obtener_matriz_simco():
    """
    Retorna el diccionario completo de las 81 reglas de SIMCO indexadas por código de material (ítem).
    Enriquece con unidad oficial, descripción limpia y tarifas contractuales.
    """
    global _REGLAS_CACHE
    if _REGLAS_CACHE is not None:
        return _REGLAS_CACHE

    reglas_raw = json.loads(REGLAS_SIMCO_RAW)

    # Mapeo de unidades desde la base de datos de Material e ItemManoObra
    items_int = [int(k) for k in reglas_raw.keys() if k.isdigit()]
    materiales_db = {str(m.item): m for m in Material.objects.filter(item__in=items_int)}
    items_mo_db = {item.codigo: item for item in ItemManoObra.objects.all()}

    matriz = {}
    for mat_code, data in reglas_raw.items():
        mat_obj = materiales_db.get(mat_code)
        unidad_mat = mat_obj.unidad if mat_obj and mat_obj.unidad else "UN"
        desc_mat = mat_obj.descripcion if mat_obj else data.get("material", "")

        actividades = []
        valor_unitario_total = Decimal("0")

        for act in data.get("manos_de_obra", []):
            mo_code = str(act.get("id_mo", "")).strip()
            mo_obj = items_mo_db.get(mo_code)
            
            val_raw = act.get("valor")
            try:
                val = Decimal(str(val_raw)) if val_raw is not None else Decimal("0")
            except Exception:
                val = Decimal("0")

            if val == 0 and mo_obj and mo_obj.valor_unitario > 0:
                val = mo_obj.valor_unitario

            mo_unidad = mo_obj.unidad if mo_obj and mo_obj.unidad else "UN"
            mo_desc = mo_obj.descripcion if mo_obj else act.get("mano_obra", "")

            valor_unitario_total += val

            actividades.append({
                "id_mo": mo_code,
                "descripcion": mo_desc,
                "unidad": mo_unidad,
                "valor_unitario": float(val)
            })

        matriz[mat_code] = {
            "item": mat_code,
            "descripcion": desc_mat,
            "unidad": unidad_mat,
            "valor_unitario_suma": float(valor_unitario_total),
            "actividades": actividades
        }

    _REGLAS_CACHE = matriz
    return _REGLAS_CACHE


def obtener_materiales_proyecto_simco(proyecto_id):
    """
    Obtiene los materiales asociados a un proyecto (tanto de MaterialRequeridoProyecto como de ApoyoMaterial)
    y los cruza con la matriz SIMCO.
    """
    proyecto = Proyecto.objects.filter(id=proyecto_id).first()
    if not proyecto:
        return {"error": "Proyecto no encontrado"}

    matriz = obtener_matriz_simco()

    # 1. Materiales requeridos (Pedidos en Logística)
    reqs = MaterialRequeridoProyecto.objects.filter(proyecto=proyecto).select_related("material")
    cantidades_req = {}
    for r in reqs:
        k = str(r.material.item)
        cantidades_req[k] = cantidades_req.get(k, Decimal("0")) + r.cantidad_requerida

    # 2. Materiales en apoyos (Instalados en Ingeniería)
    apoyos_mats = ApoyoMaterial.objects.filter(apoyo__proyecto=proyecto).select_related("material")
    cantidades_apoyo = {}
    for am in apoyos_mats:
        k = str(am.material.item)
        cantidades_apoyo[k] = cantidades_apoyo.get(k, Decimal("0")) + am.cantidad_requerida

    codigos_en_proyecto = set(cantidades_req.keys()) | set(cantidades_apoyo.keys())

    materiales_proyecto = []
    total_mano_obra_estimada = Decimal("0")

    for code in sorted(codigos_en_proyecto, key=lambda x: int(x) if x.isdigit() else 9999):
        cant_req = float(cantidades_req.get(code, Decimal("0")))
        cant_apoyo = float(cantidades_apoyo.get(code, Decimal("0")))
        cant_sugerida = cant_req if cant_req > 0 else cant_apoyo

        simco_info = matriz.get(code)
        tiene_simco = simco_info is not None

        if tiene_simco:
            val_unit_sum = simco_info["valor_unitario_suma"]
            subtotal = float(Decimal(str(cant_sugerida)) * Decimal(str(val_unit_sum)))
            total_mano_obra_estimada += Decimal(str(subtotal))

            materiales_proyecto.append({
                "item": code,
                "descripcion": simco_info["descripcion"],
                "unidad": simco_info["unidad"],
                "cantidad": cant_sugerida,
                "cantidad_pedida": cant_req,
                "cantidad_apoyos": cant_apoyo,
                "tiene_simco": True,
                "valor_unitario_suma": val_unit_sum,
                "subtotal_estimado": subtotal,
                "actividades": simco_info["actividades"]
            })
        else:
            mat_obj = Material.objects.filter(item=int(code) if code.isdigit() else 0).first()
            materiales_proyecto.append({
                "item": code,
                "descripcion": mat_obj.descripcion if mat_obj else f"Material {code}",
                "unidad": mat_obj.unidad if mat_obj else "UN",
                "cantidad": cant_sugerida,
                "cantidad_pedida": cant_req,
                "cantidad_apoyos": cant_apoyo,
                "tiene_simco": False,
                "valor_unitario_suma": 0,
                "subtotal_estimado": 0,
                "actividades": []
            })

    return {
        "proyecto_id": proyecto.id,
        "proyecto_nombre": f"{proyecto.etiqueta} {proyecto.numero_emcali}",
        "materiales": materiales_proyecto,
        "total_estimado_mano_obra": float(total_mano_obra_estimada)
    }
