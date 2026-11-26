/* Pillage the Reefer: the seas, ports, cargo and people.
   Original characters and writing. Ports are real old Caribbean harbors; the strains, people and Smoke Cay are made up. */
(function () {
  'use strict';

  var GOODS = {
    tangerine: {name: 'Tortuga Tangerine', icon: '🍊', base: 28, home: 'tortuga', note: 'Bright and citrusy. Smells like a sunny deck.'},
    purple:    {name: 'Port Royal Purple', icon: '🍇', base: 40, home: 'portroyal', note: 'Fancy. Pinky-out stuff.'},
    breath:    {name: "Buccaneer's Breath", icon: '💨', base: 32, home: 'petitgoave', note: 'Earthy and bold, like an old sea dog.'},
    haze:      {name: 'Havana Haze', icon: '🌫️', base: 44, home: 'havana', note: 'Smooth, slow and very sure of itself.'},
    nectar:    {name: 'Nassau Nectar', icon: '🍯', base: 36, home: 'nassau', note: 'Sweet as island honey.'},
    candy:     {name: 'Cartagena Candy', icon: '🍬', base: 48, home: 'cartagena', note: 'Sugary, sticky and a little bit showy.'},
    pineapple: {name: 'Portobelo Pineapple', icon: '🍍', base: 38, home: 'portobelo', note: 'Tropical. Wears a tiny hat.'},
    cloud:     {name: 'Curaçao Cloud', icon: '☁️', base: 52, home: 'willemstad', note: 'Light, fluffy and impossible to find in a hurry.'},
    vanilla:   {name: 'Veracruz Vanilla', icon: '🌼', base: 42, home: 'veracruz', note: 'Sweet, creamy and slow-cured, like a long siesta.'},
    fountain:  {name: 'Fountain of Youth', icon: '⛲', base: 46, home: 'staugustine', note: 'Makes you feel nineteen. Results not guaranteed.'},
    rumcake:   {name: 'Bajan Rum Cake', icon: '🍰', base: 40, home: 'barbados', note: 'Rich, boozy-sweet and gone too soon.'},
    kraken:    {name: 'Kraken Kush', icon: '🐙', base: 150, rare: 'Only found in the holds of merchant ships.', note: 'Legendary. Grips you with all eight arms.'},
    mermaid:   {name: "Mermaid's Kiss", icon: '🧜', base: 120, rare: 'Only found floating at sea.', note: 'Drifts in on the tide, sweet and salty.'},
    // Products: made in one port, wanted most in a few others (they pay a premium), and their prices swing by their own amount.
    hash:      {name: "Smuggler's Hash", icon: '🧱', base: 66, home: 'petitgoave', kind: 'product', swing: 0.3, wants: ['havana', 'cartagena', 'barbados'],
      note: 'Pressed bricks of resin. Strong, dense and easy to stack. Prized in Havana, Cartagena and Barbados.'},
    rosin:     {name: 'Amber Rosin', icon: '🔶', base: 84, home: 'willemstad', kind: 'product', swing: 0.5, wants: ['nassau', 'staugustine', 'veracruz'],
      note: 'Golden and glassy, squeezed by hand. Pricey, and its price jumps about from day to day. Prized in Nassau, St. Augustine and Veracruz.'},
    biscuits:  {name: "Cook's Biscuits", icon: '🍪', base: 34, home: 'nassau', kind: 'product', swing: 0.2, wants: ['tortuga', 'portobelo', 'barbados'],
      note: 'Baked by a very relaxed cook. Cheap and steady. Prized in Tortuga, Portobelo and Barbados.'}
  };
  var COMMON = ['tangerine', 'purple', 'breath', 'haze', 'nectar', 'candy', 'pineapple', 'cloud', 'vanilla', 'fountain', 'rumcake'];

  /* Land shapes, in map units. ribbon: a spine of [x, y, half-width]; blob: centre, radii, turn, seed; poly: an outline. */
  var MAPS = {
    windward: {
      name: 'The Windward Passage', short: 'Windward Passage', w: 1600, h: 1100,
      blurb: 'Between Cuba, Hispaniola and Jamaica. Home waters.',
      lands: [
        {name: 'Cuba', label: [330, 286], ribbon: [[-140, 250, 76], [100, 262, 80], [320, 285, 72], [520, 318, 60], [680, 350, 42], [790, 378, 14]]},
        {name: 'Hispaniola', label: [1300, 470], poly: [[880, 402], [945, 362], [1050, 332], [1200, 316], [1350, 320], [1500, 330], [1680, 340], [1680, 700], [1450, 690], [1250, 680], [1100, 692], [980, 702], [880, 708], [800, 712], [786, 690], [860, 662], [950, 642], [1010, 602], [1032, 540], [1000, 500], [950, 470], [905, 440]]},
        {name: 'Gonâve', blob: [925, 548, 48, 15, -0.15, 3]},
        {name: 'Tortuga', blob: [1000, 268, 58, 15, -0.05, 7]},
        {name: 'Jamaica', label: [410, 745], ribbon: [[250, 745, 30], [330, 735, 40], [430, 745, 45], [520, 765, 38], [585, 785, 20]]},
        {name: 'Navassa', blob: [705, 760, 14, 10, 0, 11]},
        {name: 'Great Inagua', label: [930, 115], blob: [930, 115, 65, 28, 0.1, 5]},
        {name: 'Little Inagua', blob: [1045, 92, 22, 12, 0.2, 6]},
        {name: 'Caicos', blob: [1460, 90, 52, 22, -0.1, 9]},
        {name: 'Île-à-Vache', blob: [960, 738, 14, 6, 0.1, 13]},
        {name: 'Morant Cays', blob: [655, 880, 10, 5, 0.3, 15]},
        {name: 'Pedro Cays', blob: [330, 885, 14, 5, -0.2, 17]},
        {name: 'Cayman Brac', blob: [70, 640, 20, 6, 0.15, 19]}
      ],
      exits: [
        {to: 'straits', rect: [0, 20, 36, 140], label: 'To the Florida Straits', at: [10, 80], arrive: [1530, 740]},
        {to: 'main', rect: [60, 1066, 1480, 34], label: 'To the Spanish Main', at: [800, 1088], arrive: ['x', 60]},
        {to: 'antilles', rect: [1564, 760, 36, 280], label: 'To the Lesser Antilles', at: [1590, 900], arrive: [70, 640]}
      ],
      arrive: {straits: [60, 90], main: ['x', 1030], antilles: [1530, 900]},
      patrols: [
        {kind: 'customs', route: [[700, 520], [880, 470], [1150, 250], [1350, 260], [880, 470], [620, 900], [300, 900], [460, 560]]},
        {kind: 'merchant', route: [[100, 560], [700, 610], [1250, 840], [1550, 960], [700, 960], [120, 640]]}
      ]
    },
    straits: {
      name: 'The Florida Straits', short: 'Florida Straits', w: 1600, h: 1100,
      blurb: 'Havana, Nassau and a thousand little cays.',
      lands: [
        {name: 'Cuba', label: [800, 900], ribbon: [[-140, 900, 62], [150, 880, 70], [380, 835, 60], [600, 815, 70], [850, 830, 78], [1100, 860, 80], [1350, 885, 80], [1720, 905, 80]]},
        {name: 'Florida', label: [215, 150], poly: [[-60, -60], [430, -60], [445, 60], [430, 170], [395, 265], [345, 330], [280, 352], [200, 330], [120, 265], [40, 225], [-60, 215]]},
        {name: 'The Keys', blob: [305, 386, 15, 5, 0.6, 21]},
        {name: 'The Keys', blob: [262, 412, 17, 5, 0.35, 22]},
        {name: 'The Keys', blob: [215, 432, 16, 5, 0.2, 23]},
        {name: 'The Keys', blob: [168, 446, 14, 4, 0.1, 24]},
        {name: 'The Keys', blob: [122, 454, 12, 4, 0, 25]},
        {name: 'Dry Tortugas', blob: [52, 480, 10, 7, 0, 26]},
        {name: 'Andros', label: [1000, 450], blob: [1000, 450, 55, 125, 0.12, 31]},
        {name: 'New Providence', blob: [1135, 335, 38, 15, 0, 33]},
        {name: 'Eleuthera', ribbon: [[1225, 250, 9], [1270, 300, 12], [1305, 370, 11], [1315, 450, 9], [1300, 520, 7]]},
        {name: 'Grand Bahama', ribbon: [[690, 140, 14], [800, 150, 18], [920, 140, 16], [1000, 118, 10]]},
        {name: 'Abaco', blob: [1125, 140, 35, 70, 0.3, 41]},
        {name: 'Bimini', blob: [700, 330, 9, 14, 0, 43]},
        {name: 'Cay Sal', blob: [690, 620, 16, 10, 0, 45]},
        {name: 'Exumas', blob: [1210, 560, 10, 6, 0.5, 46]},
        {name: 'Exumas', blob: [1240, 600, 12, 6, 0.6, 47]},
        {name: 'Exumas', blob: [1270, 640, 10, 5, 0.6, 48]},
        {name: 'Long Island', ribbon: [[1400, 500, 8], [1430, 580, 10], [1460, 650, 7]]}
      ],
      exits: [
        {to: 'windward', rect: [1564, 690, 36, 110], label: 'To the Windward Passage', at: [1590, 745], arrive: [60, 90]},
        {to: 'gulf', rect: [0, 560, 36, 220], label: 'To the Gulf of Mexico', at: [10, 670], arrive: [1530, 610]}
      ],
      arrive: {windward: [1530, 740], gulf: [60, 670]},
      patrols: [
        {kind: 'customs', route: [[300, 700], [700, 700], [620, 470], [380, 560]]},
        {kind: 'customs', route: [[1200, 400], [1380, 700], [900, 720], [860, 300]]},
        {kind: 'merchant', route: [[100, 620], [600, 700], [1000, 690], [1500, 760], [1100, 250], [500, 450]]}
      ]
    },
    main: {
      name: 'The Spanish Main', short: 'Spanish Main', w: 1600, h: 1100,
      blurb: 'Old treasure ports along the South American coast.',
      lands: [
        {name: 'South America', label: [1150, 900], poly: [[-60, 1160], [-60, 700], [70, 712], [190, 755], [290, 798], [370, 858], [425, 832], [505, 792], [590, 742], [690, 700], [810, 640], [895, 560], [945, 590], [960, 700], [985, 805], [1055, 800], [1075, 705], [1125, 640], [1175, 700], [1300, 722], [1450, 705], [1660, 722], [1660, 1160]]},
        {name: 'Curaçao', blob: [1190, 470, 44, 13, -0.35, 51]},
        {name: 'Aruba', blob: [1060, 505, 22, 8, -0.4, 53]},
        {name: 'Bonaire', blob: [1300, 445, 24, 11, 0.5, 55]},
        {name: 'Providencia', blob: [110, 250, 13, 16, 0, 57]},
        {name: 'San Andrés', blob: [70, 362, 8, 14, 0, 59]},
        {name: 'Rosario Islands', blob: [440, 735, 12, 5, 0.2, 61]},
        {name: 'Smoke Cay', label: [760, 300], blob: [760, 300, 34, 22, 0.3, 63], haze: true},
        {name: 'Margarita', blob: [1555, 560, 40, 16, 0, 65]},
        {name: 'Los Roques', blob: [1440, 470, 14, 6, 0.3, 67]},
        {name: 'Serrana Bank', blob: [330, 150, 15, 6, -0.3, 69]},
        {name: 'Roncador', blob: [230, 330, 8, 5, 0, 71]},
        {name: 'Isla de Aves', blob: [1480, 200, 9, 5, 0.4, 73]}
      ],
      exits: [
        {to: 'windward', rect: [60, 0, 1480, 34], label: 'To the Windward Passage', at: [800, 12], arrive: ['x', 1030]}
      ],
      arrive: {windward: ['x', 60]},
      patrols: [
        {kind: 'customs', route: [[300, 650], [700, 600], [1000, 420], [1300, 560], [700, 420]]},
        {kind: 'merchant', route: [[100, 500], [600, 520], [1100, 380], [1500, 640], [850, 480], [300, 420]]}
      ]
    },
    gulf: {
      name: 'The Gulf of Mexico', short: 'Gulf of Mexico', w: 1600, h: 1100,
      blurb: 'Wide open water west of Cuba, with Veracruz at the far end.',
      lands: [
        {name: 'Mexico', label: [470, 1010], poly: [[-60, -60], [210, -60], [200, 100], [180, 260], [178, 430], [195, 590], [232, 710], [285, 800], [350, 868], [440, 915], [560, 945], [700, 952], [820, 935], [880, 880], [915, 790], [955, 712], [1020, 665], [1110, 640], [1190, 648], [1240, 700], [1262, 800], [1285, 920], [1310, 1160], [-60, 1160]]},
        {name: 'The Gulf Coast', label: [720, 30], poly: [[150, -60], [1420, -60], [1400, 20], [1250, 52], [1080, 40], [900, 70], [720, 58], [540, 82], [380, 70], [250, 110], [190, 150]]},
        {name: 'Florida', label: [1540, 160], poly: [[1380, -60], [1660, -60], [1660, 400], [1600, 392], [1545, 330], [1500, 240], [1455, 140], [1410, 60]]},
        {name: 'Cuba', label: [1530, 950], ribbon: [[1330, 1010, 34], [1450, 960, 50], [1580, 925, 58], [1720, 905, 62]]},
        {name: 'Isla Mujeres', blob: [1292, 655, 6, 11, 0.3, 81]},
        {name: 'Alacranes Reef', blob: [1030, 520, 14, 7, 0.2, 83]},
        {name: 'Cayo Arcas', blob: [860, 700, 7, 5, 0, 85]},
        {name: 'Isla de Sacrificios', blob: [410, 822, 9, 5, 0.3, 87]},
        {name: 'Isla Lobos', blob: [300, 600, 7, 5, 0, 89]}
      ],
      exits: [
        {to: 'straits', rect: [1564, 470, 36, 280], label: 'To the Florida Straits', at: [1590, 610], arrive: [60, 670]}
      ],
      arrive: {straits: [1530, 610]},
      patrols: [
        {kind: 'customs', route: [[700, 400], [1100, 300], [1300, 500], [900, 560], [500, 500]]},
        {kind: 'merchant', route: [[400, 300], [1000, 200], [1450, 560], [1000, 560], [500, 700], [350, 450]]}
      ]
    },
    antilles: {
      name: 'The Lesser Antilles', short: 'Lesser Antilles', w: 1600, h: 1100,
      blurb: 'A long arc of green islands, and Barbados out on its own in the trade winds.',
      lands: [
        {name: 'Puerto Rico', label: [140, 168], ribbon: [[-80, 170, 40], [80, 165, 50], [230, 175, 46], [330, 190, 30], [370, 198, 12]]},
        {name: 'Vieques', blob: [420, 215, 14, 5, 0, 91]},
        {name: 'The Virgin Islands', blob: [470, 180, 10, 5, 0, 92]},
        {name: 'The Virgin Islands', blob: [520, 170, 10, 5, 0, 93]},
        {name: 'The Virgin Islands', blob: [480, 300, 16, 6, 0, 94]},
        {name: 'Anguilla', blob: [700, 110, 16, 5, 0.4, 95]},
        {name: 'Saint Martin', blob: [712, 150, 11, 9, 0, 96]},
        {name: 'Saba', blob: [672, 205, 6, 6, 0, 97]},
        {name: 'St. Eustatius', blob: [705, 232, 6, 6, 0, 98]},
        {name: 'St. Kitts', blob: [745, 262, 15, 7, 0.7, 99]},
        {name: 'Nevis', blob: [772, 290, 8, 8, 0, 100]},
        {name: 'Barbuda', blob: [905, 165, 15, 12, 0, 101]},
        {name: 'Antigua', label: [905, 255], blob: [905, 255, 20, 17, 0.2, 102]},
        {name: 'Montserrat', blob: [800, 325, 7, 10, 0, 103]},
        {name: 'Guadeloupe', label: [865, 395], blob: [865, 395, 32, 22, 0.2, 104]},
        {name: 'Marie-Galante', blob: [925, 440, 10, 9, 0, 105]},
        {name: 'Dominica', label: [868, 505], blob: [868, 505, 12, 24, 0.1, 106]},
        {name: 'Martinique', label: [902, 615], blob: [902, 615, 17, 28, 0.25, 107]},
        {name: 'St. Lucia', label: [935, 720], blob: [935, 720, 11, 21, 0.1, 108]},
        {name: 'St. Vincent', blob: [925, 810, 9, 15, 0.1, 109]},
        {name: 'The Grenadines', blob: [940, 850, 5, 4, 0, 110]},
        {name: 'Tobago Cays', blob: [958, 882, 6, 4, 0, 111]},
        {name: 'The Grenadines', blob: [972, 915, 6, 4, 0, 112]},
        {name: 'Grenada', label: [985, 975], blob: [985, 975, 12, 17, 0.1, 113]},
        {name: 'Barbados', label: [1400, 760], blob: [1400, 760, 19, 27, 0.15, 114]},
        {name: 'Tobago', label: [1190, 1020], blob: [1190, 1020, 22, 8, -0.4, 115]},
        {name: 'Trinidad', label: [1100, 1085], poly: [[960, 1160], [990, 1075], [1060, 1060], [1170, 1072], [1230, 1100], [1240, 1160]]}
      ],
      exits: [
        {to: 'windward', rect: [0, 360, 36, 620], label: 'To the Windward Passage', at: [10, 640], arrive: [1530, 900]}
      ],
      arrive: {windward: [70, 640]},
      patrols: [
        {kind: 'customs', route: [[600, 500], [1100, 600], [1250, 850], [700, 900], [400, 650]]},
        {kind: 'merchant', route: [[150, 700], [700, 750], [1300, 600], [1500, 900], [1050, 950], [300, 900]]}
      ]
    }
  };

  /* Ports. dock: where the ship ties up (water); town: where the houses are drawn (land). */
  var PORTS = {
    tortuga:    {name: 'Tortuga', map: 'windward', dock: [1000, 302], town: [1000, 272], sells: ['tangerine', 'breath', 'purple'], yard: true, who: 'ruthie',
                 blurb: 'A rocky little island full of hammocks, gossip and suspicious-smelling smoke.'},
    portroyal:  {name: 'Port Royal', map: 'windward', dock: [545, 832], town: [532, 798], sells: ['purple', 'tangerine', 'breath'], yard: true, who: 'percival',
                 blurb: 'The richest, rowdiest harbor in the Caribbean. The wigs are very tall here.'},
    petitgoave: {name: 'Petit-Goâve', map: 'windward', dock: [985, 598], town: [994, 630], sells: ['breath', 'tangerine', 'pineapple', 'hash'], yard: false, who: 'toussaint',
                 blurb: 'A quiet old buccaneer harbor where everyone is mending a net or pretending to.'},
    havana:     {name: 'Havana', map: 'straits', dock: [385, 746], town: [385, 792], sells: ['haze', 'nectar', 'fountain'], yard: true, who: 'catalina',
                 blurb: 'Grand walls, grand ships and the finest rollers on any sea.'},
    nassau:     {name: 'Nassau', map: 'straits', dock: [1132, 300], town: [1135, 334], sells: ['nectar', 'haze', 'tangerine', 'biscuits'], yard: false, who: 'mildew',
                 blurb: 'A pirate republic of palm trees, hammocks and very relaxed rules.'},
    cartagena:  {name: 'Cartagena', map: 'main', dock: [500, 758], town: [508, 806], sells: ['candy', 'pineapple', 'cloud'], yard: true, who: 'quill',
                 blurb: 'A walled city of balconies, bells and one very busy botanist.'},
    portobelo:  {name: 'Portobelo', map: 'main', dock: [180, 724], town: [182, 770], sells: ['pineapple', 'candy', 'breath'], yard: false, who: 'prudence',
                 blurb: 'Sleepy treasure port. Somebody important is on holiday here.'},
    willemstad: {name: 'Willemstad', map: 'main', dock: [1196, 502], town: [1192, 472], sells: ['cloud', 'candy', 'nectar', 'rosin'], yard: true, who: 'ines',
                 blurb: 'Colorful houses, a floating bridge and a famous captain in retirement.'},
    staugustine: {name: 'St. Augustine', map: 'straits', dock: [482, 75], town: [418, 52], sells: ['fountain', 'nectar', 'tangerine'], yard: false, who: 'bartholomew',
                 blurb: 'The oldest town in Florida. Some of the residents feel it.'},
    veracruz:   {name: 'Veracruz', map: 'gulf', dock: [322, 790], town: [266, 820], sells: ['vanilla', 'haze', 'fountain'], yard: true, who: 'esperanza',
                 blurb: 'A busy old harbor that smells of vanilla, tar and very long lunches.'},
    barbados:   {name: 'Barbados', map: 'antilles', dock: [1362, 800], town: [1398, 768], sells: ['rumcake', 'cloud', 'pineapple'], yard: true, who: 'clementine',
                 blurb: 'Bridgetown, on Carlisle Bay. Flying fish, cricket and a rum shop that never seems to close.'}
  };

  /* Buried treasure. A rumor marks the spot on your chart; the Emerald Bale needs all three map pieces. */
  var STASHES = {
    s1: {name: 'Navassa', map: 'windward', at: [705, 760], piece: true, gold: 150, loot: {mermaid: 3},
         text: 'You dig past three goats and one very offended crab. Clunk! A chest! Inside: the first piece of Captain Featherstone’s map, 150 doubloons and 3 bales of Mermaid’s Kiss.'},
    s2: {name: 'the Dry Tortugas', map: 'straits', at: [52, 480], piece: true, gold: 250, loot: {kraken: 1},
         text: 'Under a palm tree shaped like a question mark you find the second piece of the map, 250 doubloons and a bale of Kraken Kush.'},
    s3: {name: 'Providencia', map: 'main', at: [110, 250], piece: true, gold: 300, loot: {kraken: 2},
         text: 'Behind a rock that looks like a sleeping landlord: the third piece of the map, 300 doubloons and 2 bales of Kraken Kush.'},
    alacranes: {name: 'the Alacranes Reef', map: 'gulf', at: [1030, 520], gold: 300, loot: {mermaid: 2},
         text: 'A very rude seagull watches you dig. Clunk! A little chest: 300 doubloons and 2 bales of Mermaid’s Kiss. The seagull takes one biscuit as tax.'},
    tobagocays: {name: 'the Tobago Cays', map: 'antilles', at: [958, 882], gold: 350, loot: {kraken: 1},
         text: 'Between two turtles and a very confused pelican you find a chest: 350 doubloons and a bale of Kraken Kush.'},
    emerald: {name: 'Smoke Cay', map: 'main', at: [760, 300], needs: 3, gold: 2000, loot: {},
         text: 'The haze parts. You dig, and dig, and… there it is: the Emerald Bale, wrapped in old sailcloth and smelling like every good day you ever had. Under it, 2,000 doubloons and a note in Ines’s hand: “Share some.”'}
  };

  /* People. Each node: text, then options. Options may need a condition (if) and may do something (do). */
  var PEOPLE = {
    ruthie: {
      name: 'Mama Ruthie Barnacle', role: 'Keeper of the Leaky Lantern tavern', icon: '🍺', port: 'tortuga',
      start: {text: 'Well, well. A fresh captain with an empty hold and a parrot full of opinions. Welcome to Tortuga, love. What’ll it be?', options: [
        {label: 'How does a pirate make a living around here?', next: 'trade'},
        {label: 'Heard any good rumors?', next: 'rumor', if: '!hint:s1'},
        {label: 'Tell me that rumor again.', next: 'rumor2', if: 'hint:s1'},
        {label: 'Where can a ship go from here?', next: 'where'},
        {label: 'Just passing through.', end: true}]},
      trade: {text: 'Buy it cheap where it grows, sell it dear where it doesn’t. Tortuga Tangerine grows like a weed here, mostly because it is one. Haul it somewhere fancy, like Havana or the Spanish Main, and watch the coin roll in.', options: [{label: 'Buy low, sell high. Got it.', next: 'start'}]},
      rumor: {text: 'Old Captain Ines Featherstone grew the finest crop that ever sailed: the Emerald Bale. Before she retired she buried it and tore her map in three. One piece is on Navassa, a lonely rock south-west of here. Only goats live there. Very judgmental goats.', do: 'hint:s1', options: [{label: 'I’ll go have a look.', next: 'start'}]},
      rumor2: {text: 'Navassa, love. South-west, between here and Jamaica. Follow the smell of goat.', options: [{label: 'Thanks, Ruthie.', next: 'start'}]},
      where: {text: 'Sail west past the tip of Cuba for the Florida Straits: Havana and Nassau. Sail off the bottom of the chart for the Spanish Main: Cartagena and friends. Sail east past Hispaniola for the Lesser Antilles and Barbados. Mind the Crown Customs cutters, with their blue sails, and the pirates with black ones. Neither has a sense of humor.', do: 'know:havana,know:cartagena,know:barbados', options: [{label: 'Blue sails, black sails. Noted.', next: 'start'}]}
    },
    percival: {
      name: 'Lord Percival Fopsworth III', role: 'Gentleman of delicate constitution', icon: '🎩', port: 'portroyal',
      start: {text: 'Ah! A sea captain. Do not be alarmed by my wig; it is perfectly normal for it to be this tall. I require… medicine. For my gout. It is extremely medicinal.', options: [
        {label: 'What kind of medicine?', next: 'ask', if: '!quest:percival'},
        {label: 'Here’s your Havana Haze.', next: 'done', if: 'can:percival'},
        {label: 'How is the gout?', next: 'after', if: 'done:percival'},
        {label: 'Any news in Port Royal?', next: 'news'},
        {label: 'Good day, my lord.', end: true}]},
      ask: {text: 'Havana Haze. Five bales. My physician insists, and my physician is also me. Bring them and I shall pay three hundred doubloons, which I am told is a lot of money.', options: [
        {label: 'Deal.', do: 'quest:percival', next: 'start'}, {label: 'Maybe later.', next: 'start'}]},
      done: {text: 'Splendid! My gout already feels… wiggly. Three hundred doubloons, as promised. Tell no one. Especially my mother.', do: 'complete:percival', options: [{label: 'My lips are sealed.', next: 'start'}]},
      after: {text: 'Never better. I have taken up interpretive dance. The servants are concerned.', options: [{label: 'Glad to hear it.', next: 'start'}]},
      news: {text: 'They say the Customs Commodore takes her holidays in Portobelo. Even the law needs a nap, apparently.', do: 'know:portobelo', options: [{label: 'Interesting.', next: 'start'}]}
    },
    toussaint: {
      name: 'Grandpère Toussaint', role: 'Retired buccaneer, part-time net mender', icon: '🎣', port: 'petitgoave',
      start: {text: 'Sit, sit. Forty years I sailed these waters. Now I mend nets and tell stories. Mostly the stories. The nets are a mess.', options: [
        {label: 'Tell me about pillaging.', next: 'pillage'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:toussaint'},
        {label: 'Two bales of Mermaid’s Kiss, as promised.', next: 'done', if: 'can:toussaint'},
        {label: 'Farewell, Grandpère.', end: true}]},
      pillage: {text: 'Fat merchant ships waddle across the sea like ducks full of bread. Sail right into one and you can try boarding her. More cannons, better odds. Cannons are what pirates have instead of manners.', options: [{label: 'Ducks full of bread. Got it.', next: 'start'}]},
      ask: {text: 'Mermaid’s Kiss. The bales that float in on the tide, sweet as island honey. Keep your eyes on the water. Bring me two and I’ll pay three hundred fifty doubloons and tell you a story.', options: [
        {label: 'You’ve got a deal.', do: 'quest:toussaint', next: 'start'}, {label: 'Not today.', next: 'start'}]},
      done: {text: 'Ahh. Smells like the good old days. Here is your gold. And the story: never trust a goat. That is the whole story.', do: 'complete:toussaint', options: [{label: 'Words to live by.', next: 'start'}]}
    },
    catalina: {
      name: 'Doña Catalina Humo', role: 'Master roller of Havana', icon: '🍃', port: 'havana',
      start: {text: 'Everyone thinks they can roll. Everyone is wrong. Welcome to Havana, Captain. Do not touch anything on my table.', options: [
        {label: 'Can you teach me to roll?', next: 'teach'},
        {label: 'Need anything shipped?', next: 'ask', if: '!quest:catalina'},
        {label: 'Ten bales of Tortuga Tangerine, Doña.', next: 'done', if: 'can:catalina'},
        {label: 'Adiós.', end: true}]},
      teach: {text: 'No. But I will tell you this for free: Havana pays well for Port Royal Purple, and the Customs cutters here are thick as mosquitoes. Pay them, outrun them or outsmart them. Never cry in front of them. Oh, and Nassau buys anything. Anything. And west of here, past the edge of the chart, Veracruz grows a vanilla people write poems about.', do: 'know:nassau,know:veracruz', options: [{label: 'No crying. Understood.', next: 'start'}]},
      ask: {text: 'Ten bales of Tortuga Tangerine. I am experimenting with citrus notes. Four hundred doubloons.', options: [
        {label: 'Consider it done.', do: 'quest:catalina', next: 'start'}, {label: 'Another time.', next: 'start'}]},
      done: {text: 'Perfect. Bright as a sunrise. Four hundred doubloons, and you may now touch exactly one thing on my table. Not that one.', do: 'complete:catalina', options: [{label: 'Gracias.', next: 'start'}]}
    },
    mildew: {
      name: 'Captain Mildred “Mildew” Mudge', role: 'Retired pirate, professional hammock tester', icon: '🏝️', port: 'nassau',
      start: {text: 'Shh. I’m resting. I’ve been resting for about thirty years. Big job, resting.', options: [
        {label: 'Any treasure around here?', next: 'treasure', if: '!hint:s2'},
        {label: 'Where was that treasure again?', next: 'again', if: 'hint:s2'},
        {label: 'Why do they call you Mildew?', next: 'name'},
        {label: 'Anything up the Florida coast?', next: 'florida'},
        {label: 'Sweet dreams.', end: true}]},
      florida: {text: 'St. Augustine, up the coast to the north-west. Fella there says he’s three hundred years old. Never once seen him in a hammock, so I don’t trust him.', do: 'know:staugustine', options: [{label: 'Noted.', next: 'start'}]},
      treasure: {text: 'Mmh. Ines Featherstone hid a piece of her map on the Dry Tortugas, way out west past the Florida Keys. I’d fetch it myself, but this hammock isn’t going to lie in itself.', do: 'hint:s2', options: [{label: 'Thanks, Mildew.', next: 'start'}]},
      again: {text: 'Dry Tortugas. West. Past the Keys. Shh.', options: [{label: 'Shh. Right.', next: 'start'}]},
      name: {text: 'I have been in this hammock a long time, Captain. A long, long time.', options: [{label: 'Fair enough.', next: 'start'}]}
    },
    quill: {
      name: 'Professor Ignatius Quill', role: 'Botanist, author, enthusiast', icon: '📚', port: 'cartagena',
      start: {text: 'Fascinating! A specimen! I mean, a visitor. I’m cataloguing every strain in the Caribbean for my book, Leaves of Considerable Interest.', options: [
        {label: 'Tell me about your book.', next: 'book'},
        {label: 'Seen any old maps?', next: 'maps', if: '!hint:s3'},
        {label: 'Where was that map piece again?', next: 'again', if: 'hint:s3'},
        {label: 'Who else should I meet?', next: 'who'},
        {label: 'Need a specimen?', next: 'ask', if: '!quest:quill'},
        {label: 'One bale of Kraken Kush, Professor.', next: 'done', if: 'can:quill'},
        {label: 'Good luck with the book.', end: true}]},
      who: {text: 'Captain Ines Featherstone herself! She retired to Willemstad on Curaçao, east along the coast. She grows Curaçao Cloud now and refuses to talk about treasure. Mostly.', do: 'know:willemstad', options: [{label: 'Willemstad. Thanks.', next: 'start'}]},
      book: {text: 'Volume one is two thousand pages. Volume two is mostly sketches of leaves. Volume three is a cry for help.', options: [{label: 'I’ll wait for the movie.', next: 'start'}]},
      maps: {text: 'Indeed! I found Captain Featherstone’s notes in the city archive. Her third map piece is on Providencia, the little island far to the north-west. Pirates loved it. Lots of hiding places and very few landlords.', do: 'hint:s3', options: [{label: 'Providencia. Thank you!', next: 'start'}]},
      again: {text: 'Providencia! North-west! Do take notes, Captain.', options: [{label: 'Noted.', next: 'start'}]},
      ask: {text: 'The legendary Kraken Kush! Only ever found in the holds of merchant ships. Bring me one bale and I’ll pay six hundred doubloons. For science.', options: [
        {label: 'For science!', do: 'quest:quill', next: 'start'}, {label: 'Science can wait.', next: 'start'}]},
      done: {text: 'Magnificent! Tentacular! Six hundred doubloons, and a footnote in volume four.', do: 'complete:quill', options: [{label: 'A footnote! I’m honored.', next: 'start'}]}
    },
    prudence: {
      name: 'Commodore Prudence Pinchwhistle', role: 'Crown Customs, on holiday', icon: '👒', port: 'portobelo',
      start: {text: 'I am on holiday, Captain. So I did not see your cargo, and you did not see me in this straw hat. Agreed?', options: [
        {label: 'Agreed.', next: 'tip'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:prudence'},
        {label: 'Eight bales of Curaçao Cloud, Commodore.', next: 'done', if: 'can:prudence'},
        {label: 'Enjoy your holiday.', end: true}]},
      tip: {text: 'Good. A little tip, between friends I am pretending not to have: my officers can be bribed, outrun or confused. Polite captains confuse them more often.', options: [{label: 'Very helpful.', next: 'start'}]},
      ask: {text: 'Eight bales of Curaçao Cloud. It is for… evidence. Very important evidence, which I will be evaluating on this beach. Five hundred doubloons.', options: [
        {label: 'Happy to help the law.', do: 'quest:prudence', next: 'start'}, {label: 'Maybe later.', next: 'start'}]},
      done: {text: 'This evidence is extremely thorough. Five hundred doubloons, and I will tell my cutters you are a vicar. They will be much less nosy.', do: 'complete:prudence', options: [{label: 'Bless you, Commodore.', next: 'start'}]}
    },
    ines: {
      name: 'Captain Ines Featherstone', role: 'Legendary grower, happily retired', icon: '🦜', port: 'willemstad',
      start: {text: 'So you’re the one sailing about digging up my old map. Good. I’m too old to dig. My knees retired before I did.', options: [
        {label: 'Why did you tear up the map?', next: 'why'},
        {label: 'Where are the pieces?', next: 'pieces', if: '!pieces:3'},
        {label: 'I have all three pieces!', next: 'three', if: 'pieces:3', also: '!found:emerald'},
        {label: 'I found the Emerald Bale!', next: 'won', if: 'found:emerald'},
        {label: 'Farewell, Captain.', end: true}]},
      why: {text: 'To see if anyone was worth it. Also, I was very relaxed that evening and it seemed like a wonderful idea.', options: [{label: 'Fair.', next: 'start'}]},
      pieces: {text: 'One on Navassa, one on the Dry Tortugas, one on Providencia. Bring them together and look for the cay that’s always wrapped in smoke.', do: 'hint:s1,hint:s2,hint:s3', options: [{label: 'Thank you, Captain.', next: 'start'}]},
      three: {text: 'All three! Then you know where to go: Smoke Cay, out in the open sea north of the Main. Follow the haze. The Emerald Bale is yours if you can dig it up.', options: [{label: 'I’m on my way.', next: 'start'}]},
      won: {text: 'Ha! Then you’re a Legend of the Reefer now. Try not to let it go to your head. It went to mine for about forty years.', options: [{label: 'I’ll try.', next: 'start'}]}
    },
    bartholomew: {
      name: 'Brother Bartholomew Spry', role: 'Says he is 312 years old', icon: '⛲', port: 'staugustine',
      start: {text: 'Welcome to St. Augustine, the oldest town in Florida! I’m Brother Bartholomew, and I’m three hundred and twelve years old. I drank from the fountain. Don’t tell anyone. Tell everyone.', options: [
        {label: 'Three hundred and twelve? Really?', next: 'age'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:bartholomew'},
        {label: 'Five bales of Veracruz Vanilla, Brother.', next: 'done', if: 'can:bartholomew'},
        {label: 'Where else should I sail?', next: 'where'},
        {label: 'Farewell, Brother.', end: true}]},
      age: {text: 'Give or take a century. The secret is the Fountain of Youth, a good nap and never, ever arguing with a pelican.', options: [{label: 'Words to live by.', next: 'start'}]},
      ask: {text: 'I’m turning three hundred and thirteen! I need a cake, and a cake needs vanilla. Five bales of Veracruz Vanilla, from the Gulf of Mexico. Three hundred fifty doubloons.', options: [
        {label: 'Happy early birthday. Deal.', do: 'quest:bartholomew', next: 'start'}, {label: 'Maybe later.', next: 'start'}]},
      done: {text: 'Vanilla! It smells exactly like my two hundredth birthday. Three hundred fifty doubloons, and a candle for your trouble. Just the one. We’d need a bigger cake.', do: 'complete:bartholomew', options: [{label: 'Many happy returns.', next: 'start'}]},
      where: {text: 'West, past Havana and off the edge of the chart, lies the Gulf of Mexico. Veracruz is at the far end. Lovely people. Very long lunches.', do: 'know:veracruz', options: [{label: 'Thanks, Brother.', next: 'start'}]}
    },
    esperanza: {
      name: 'Doña Esperanza Vainilla', role: 'Vanilla grower and dessert critic', icon: '🌼', port: 'veracruz',
      start: {text: 'Smell that, Captain? Vanilla. Veracruz grows the best in the world, and I will fight anyone who says otherwise. Politely.', options: [
        {label: 'What makes it so special?', next: 'vanilla'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:esperanza'},
        {label: 'Four bales of Bajan Rum Cake, Doña.', next: 'done', if: 'can:esperanza'},
        {label: 'Heard any rumors?', next: 'rumor', if: '!hint:alacranes'},
        {label: 'Where was that reef again?', next: 'again', if: 'hint:alacranes'},
        {label: 'Adiós, Doña.', end: true}]},
      vanilla: {text: 'Patience. Every pod is cured in the sun for months. It is the slowest crop on earth, which is why everyone here takes very long lunches. Sell it far away. In Barbados they go wild for it.', do: 'know:barbados', options: [{label: 'Patience. Got it.', next: 'start'}]},
      ask: {text: 'I am inventing the perfect dessert, and it needs Bajan Rum Cake, all the way from Barbados. Four bales, and I pay four hundred fifty doubloons. You also get the first bite.', options: [
        {label: 'For dessert!', do: 'quest:esperanza', next: 'start'}, {label: 'Another time.', next: 'start'}]},
      done: {text: 'Rum, sugar, butter, more rum. Perfect. Four hundred fifty doubloons, and the first bite is yours. A small bite.', do: 'complete:esperanza', options: [{label: 'Delicious.', next: 'start'}]},
      rumor: {text: 'Fishermen say an old captain buried a chest on the Alacranes Reef, north of the Yucatán. They also say a very rude seagull lives there, so be quick.', do: 'hint:alacranes', options: [{label: 'I’ll bring biscuits.', next: 'start'}]},
      again: {text: 'The Alacranes Reef, north of the Yucatán. Mind the seagull.', options: [{label: 'Gracias.', next: 'start'}]}
    },
    clementine: {
      name: 'Auntie Clementine Flyingfish', role: 'Runs the rum shop on Carlisle Bay', icon: '🐟', port: 'barbados',
      start: {text: 'Come in out of the sun, Captain, you look peaky. Sit down, eat something, and then we can talk business.', options: [
        {label: 'What’s good in Barbados?', next: 'good'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:clementine'},
        {label: 'Four bales of Fountain of Youth, Auntie.', next: 'done', if: 'can:clementine'},
        {label: 'Any buried treasure around here?', next: 'treasure', if: '!hint:tobagocays'},
        {label: 'Where was that treasure again?', next: 'again', if: 'hint:tobagocays'},
        {label: 'Thank you, Auntie.', end: true}]},
      good: {text: 'Flying fish, rum cake and cricket, in that order. Bajan Rum Cake sells well anywhere far from here, and the farther the better.', options: [{label: 'Far away. Got it.', next: 'start'}]},
      ask: {text: 'My mother is ninety-four and has decided she would like to be ninety-three. I hear St. Augustine grows something called Fountain of Youth. Four bales, four hundred doubloons, and she will stop calling you skinny.', options: [
        {label: 'Anything for your mother.', do: 'quest:clementine', next: 'start'}, {label: 'Not today.', next: 'start'}]},
      done: {text: 'She is ninety-three already and out dancing! Four hundred doubloons, Captain, and a slice of cake for the road.', do: 'complete:clementine', options: [{label: 'Give her my best.', next: 'start'}]},
      treasure: {text: 'My grandfather swore a pirate buried a chest in the Tobago Cays, the little islands down in the Grenadines. He also swore he once outswam a shark, so take it how you like.', do: 'hint:tobagocays', options: [{label: 'I’ll take a look.', next: 'start'}]},
      again: {text: 'The Tobago Cays, down in the Grenadines, south of St. Vincent.', options: [{label: 'Thank you.', next: 'start'}]}
    }
  };

  /* Delivery requests: who asks, what for, and the reward. */
  var QUESTS = {
    percival:  {by: 'percival', port: 'portroyal', good: 'haze', n: 5, gold: 300},
    toussaint: {by: 'toussaint', port: 'petitgoave', good: 'mermaid', n: 2, gold: 350},
    catalina:  {by: 'catalina', port: 'havana', good: 'tangerine', n: 10, gold: 400},
    quill:     {by: 'quill', port: 'cartagena', good: 'kraken', n: 1, gold: 600},
    prudence:  {by: 'prudence', port: 'portobelo', good: 'cloud', n: 8, gold: 500},
    bartholomew: {by: 'bartholomew', port: 'staugustine', good: 'vanilla', n: 5, gold: 350},
    esperanza: {by: 'esperanza', port: 'veracruz', good: 'rumcake', n: 4, gold: 450},
    clementine: {by: 'clementine', port: 'barbados', good: 'fountain', n: 4, gold: 400}
  };

  var UPGRADES = {
    hold:     {name: 'Bigger hold', icon: '📦', levels: [20, 30, 45, 65, 90], cost: [400, 1200, 2800, 6000], note: 'Room for more bales.'},
    hull:     {name: 'Stouter hull', icon: '🛡️', levels: [30, 45, 65, 90], cost: [400, 1400, 3500], note: 'More hull points, so you last longer in a fight.'},
    cannons:  {name: 'More cannons', icon: '💣', levels: [0, 1, 2, 3, 4], cost: [300, 1000, 2600, 5500], note: 'Every broadside hits harder, and warning shots land better.'},
    crew:     {name: 'Hire boarders', icon: '👥', levels: [0, 1, 2, 3], cost: [400, 1300, 3200], note: 'Better odds when you board, and more hands to carry off loot.'},
    sails:    {name: 'Faster sails', icon: '⛵', levels: [0, 1, 2, 3], cost: [500, 1500, 3800], note: 'Sail faster, and outrun Customs and pirates more often.'},
    lavender: {name: 'Lavender-lined hold', icon: '🌸', levels: [0, 1], cost: [900], note: 'Customs can’t smell your cargo from as far away.'}
  };

  /* Renown earns levels. Every level after the first gives a skill point. */
  var LEVELS = [
    {xp: 0, title: 'Deckhand'}, {xp: 60, title: 'Powder Monkey'}, {xp: 180, title: 'Bosun'}, {xp: 380, title: 'Navigator'},
    {xp: 680, title: 'Quartermaster'}, {xp: 1100, title: 'First Mate'}, {xp: 1650, title: 'Captain'}, {xp: 2350, title: 'Sea Wolf'},
    {xp: 3250, title: 'Commodore'}, {xp: 4400, title: 'Pirate Lord'}
  ];
  var SKILLS = {
    fight: {name: 'Fighting', icon: '⚔️', note: 'Harder broadsides and better boarding odds.'},
    sail:  {name: 'Sailing', icon: '🧭', note: 'A faster ship and better odds when you run.'},
    charm: {name: 'Charm', icon: '🗣️', note: 'Better prices, cheaper bribes and smoother talking.'}
  };
  var SKILL_MAX = 5;

  /* How rough each sea is: it sets how tough the pirates are and how rich the loot. */
  var SEA_TIER = {windward: 1, straits: 2, antilles: 2, gulf: 3, main: 3};
  var PIRATE_COUNT = {windward: 1, straits: 1, antilles: 2, gulf: 2, main: 2};
  var PIRATE_SHIPS = ['the Salty Grudge', 'the Crooked Grin', 'the Wet Sock', 'the Bad Idea', 'the Second Helping', 'the Loud Neighbour',
    'the Unpaid Invoice', 'the Sore Loser', 'the Petty Theft', 'the Last Straw'];
  var PIRATE_CAPTAINS = ['One-Eyed Edna Bramble', 'Barnaby “Bilge” Crumb', 'Scurvy Sal Tuckett', 'Gentleman Jeb Mortimer', 'Two-Hat Tilly Ross',
    'Ol’ Gums McGrady', 'Red Rosalind Fitch', 'Hobb the Nailbiter', 'Lady Winifred Rust', 'Short Pete Lomax'];
  var BOSS = {captain: 'Captain Silas Gristle', ship: 'the Bitter End', map: 'main', level: 7, gold: 2500, loot: {kraken: 3},
    intro: 'Black sails, red trim and a figurehead that is rude on purpose. Captain Silas Gristle, terror of the Spanish Main, has heard about you and does not like it.'};

  var CUSTOMS_NAMES = ['Lieutenant Dudley Clipboard', 'Ensign Agatha Stamp', 'Sergeant Percy Paperwork', 'Lieutenant Mabel Inkwell', 'Ensign Rupert Triplicate'];
  var MERCHANT_NAMES = ['the Prosperous Penny', 'the Comfortable Shoe', 'the Sensible Investment', 'the Mild Surprise', 'the Quarterly Report', 'the Reasonable Doubt', 'the Polite Cough'];

  /* Notes in bottles when no joke is to hand. */
  var BOTTLE_TIPS = [
    'The note reads: “Prices change every day. If a port won’t pay what you want, try again tomorrow, or try the next sea over.”',
    'The note reads: “Goods from another sea fetch the best prices. Tortuga Tangerine in Cartagena? Chef’s kiss.”',
    'The note reads: “Merchant ships carry Kraken Kush. Customs cutters carry clipboards. Choose your fights.”',
    'The note reads: “Black sails mean pirates. Pound them with broadsides first, then board when they’re weak.”',
    'The note reads: “A pirate who beats you only takes part of your hold. Patch up at any port and try again.”',
    'The note reads: “Whoever finds this: the haze over Smoke Cay never lifts. Signed, someone who got lost there for a week.”',
    'The note reads: “Pressed hash from Petit-Goâve fetches a fortune in Havana. Write down every price you see. Your ledger is your best friend.”',
    'The note reads: “Every strain gives a different buzz. Smoke a bale of Cartagena Candy before a tricky bit of business.”'
  ];

  /* Smoking (or eating) one bale gives a short boost for about two days of sailing. One boost at a time: a new one replaces the old.
     fight, sail, charm: extra skill points. luck: added to every odds check. sell: extra on every sale. speed: faster sailing.
     nose: how close Customs must get to smell you. calm: pirates leave you be. mend: 1 hull point a league. sight: see farther. comb: more floating bales. */
  var SMOKE = {
    tangerine: {name: 'Sunny Sails', sail: 2, does: '+2 Sailing: a faster ship and better odds when you run.', flavor: 'The whole deck smells like a sunny morning.'},
    purple:    {name: 'Pinky Out', charm: 2, does: '+2 Charm: better prices, cheaper bribes and smoother talking.', flavor: 'Everyone starts speaking very properly.'},
    breath:    {name: 'Old Sea Dog', fight: 2, does: '+2 Fighting: harder broadsides and better boarding odds.', flavor: 'Your crew starts growling at seagulls.'},
    haze:      {name: 'Low Profile', nose: 0.5, does: 'Customs have to sail twice as close to smell your cargo.', flavor: 'You feel smooth, slow and very hard to notice.'},
    nectar:    {name: 'Honey Hands', mend: 1, does: 'Your mellow crew patches 1 hull point for every league you sail.', flavor: 'Somebody starts humming and picks up a hammer.'},
    candy:     {name: 'Sugar Rush', luck: 0.1, does: '+10% on every odds check.', flavor: 'Everything feels like it’s going to work out.'},
    pineapple: {name: 'Party Hat', sell: 0.08, does: 'Buyers love you: +8% on everything you sell.', flavor: 'A tiny hat appears on your head. Nobody knows where from.'},
    cloud:     {name: 'Head in the Clouds', sight: 1.6, does: 'You see much farther, so the fog lifts faster.', flavor: 'The horizon looks very, very interesting.'},
    vanilla:   {name: 'Siesta', calm: 1, does: 'Pirates are too relaxed to bother you.', flavor: 'A great calm settles over the sea. Even the pirates yawn.'},
    fountain:  {name: 'Feeling Nineteen', sail: 1, charm: 1, fight: 1, does: '+1 Fighting, Sailing and Charm.', flavor: 'You feel young, bold and a bit reckless.'},
    rumcake:   {name: 'Beachcomber', comb: 1, does: 'Floating bales turn up twice as often.', flavor: 'You develop a keen eye for anything bobbing in the water.'},
    kraken:    {name: 'Eight Arms', fight: 2, sail: 2, charm: 2, luck: 0.1, does: '+2 to every skill and +10% on every odds check.', flavor: 'You feel like you could hold eight cutlasses at once.'},
    mermaid:   {name: 'Swims Like a Fish', speed: 0.25, does: 'Your ship sails 25% faster.', flavor: 'Salt spray, sweet air and a sudden urge to sing.'},
    hash:      {name: 'Iron Nerves', fight: 2, luck: 0.05, does: '+2 Fighting and +5% on every odds check.', flavor: 'Heavy, slow and steady. Nothing rattles you.'},
    rosin:     {name: 'Golden Glow', charm: 2, sell: 0.05, does: '+2 Charm and +5% on everything you sell.', flavor: 'You glow. Literally, a little. It’s fine.'},
    biscuits:  {name: 'Slow Burn', sail: 1, charm: 1, fight: 1, days: 4, verb: 'eat', does: '+1 Fighting, Sailing and Charm, and it lasts twice as long.', flavor: 'Nothing happens for an hour. Then everything is lovely for days.'}
  };

  var PARROT = 'Admiral Biscuit';

  window.PILLAGE_DATA = {GOODS: GOODS, COMMON: COMMON, MAPS: MAPS, PORTS: PORTS, STASHES: STASHES, PEOPLE: PEOPLE,
    QUESTS: QUESTS, UPGRADES: UPGRADES, LEVELS: LEVELS, SKILLS: SKILLS, SKILL_MAX: SKILL_MAX, SEA_TIER: SEA_TIER,
    PIRATE_COUNT: PIRATE_COUNT, PIRATE_SHIPS: PIRATE_SHIPS, PIRATE_CAPTAINS: PIRATE_CAPTAINS, BOSS: BOSS,
    CUSTOMS_NAMES: CUSTOMS_NAMES, MERCHANT_NAMES: MERCHANT_NAMES, BOTTLE_TIPS: BOTTLE_TIPS, SMOKE: SMOKE, PARROT: PARROT};
})();
