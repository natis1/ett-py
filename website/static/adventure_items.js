function addItems(){
    var placeholders = ["Boots of Bouncing (Greater)", "Unstoppable Rod", "Immovable Object",
    "Steam Deck of Many Things", "Kemono Mask", "Wonderless Figurine (Orange Hyena)", "Eldest Seed",
    "Triangular Sawtooth", "Enveloping Blight", "Aeon Stone (Puke Green)", "Bread Ampule (Lesser)",
    "Mary Jane", "Uranium-235", "Critical Fumble Deck", "Pocket Mansion",
    "Smartphone", "Circus in a Box", "The Game Mastery's Guide", "Curse of the First Dragon",
    "Ant"]
    var number = document.getElementById("itemsNr").value;
    if (number > 20) {
        number = 20;
    }
    var container = document.getElementById("item-container");
    while (container.hasChildNodes()) {
        container.removeChild(container.lastChild);
    }
    for (i=0; i<number; i++){
        var row1 = document.createElement("div");
        row1.classList.add("row");
        var name_label = document.createElement("label");
        name_label.htmlFor = "items[][name]";
        name_label.innerHTML = "Item " + (i+1) + " Name";
        name_label.classList.add('column');
        var name = document.createElement("input");
        name.minlength="2"
        name.maxlength="32"
        name.type = "text";
        name.name = "items[][name]";
        name.id = "items[][name]";
        name.placeholder = placeholders[i]
        name.classList.add('form-control');
        name.classList.add('column');
        row1.appendChild(name_label);
        row1.appendChild(name);
        container.appendChild(row1);

        var row2 = document.createElement("div");
        row2.classList.add("row");
        var level_label = document.createElement("label");
        level_label.htmlFor = "items[][level]";
        level_label.innerHTML = "Level";
        level_label.classList.add('column');
        var level = document.createElement("input");
        level.required = true;
        level.type = "number";
        level.step = "1";
        level.min = "0";
        level.max = "30";
        level.name = "items[][level]";
        level.id = "items[][level]";
        level.placeholder = "0";
        level.classList.add('form-control');
        level.classList.add('column');
        row2.appendChild(level_label);
        row2.appendChild(level);
        container.appendChild(row2);

        var row3 = document.createElement("div");
        row3.classList.add("row");
        var cost_label = document.createElement("label");
        cost_label.htmlFor = "items[][cost]";
        cost_label.innerHTML = "Cost";
        cost_label.classList.add('column');
        var cost = document.createElement("input");
        cost.required = true;
        cost.type = "number";
        cost.step = "0.01";
        cost.min = "0";
        cost.max = "999999";
        cost.name = "items[][cost]";
        cost.id = "items[][cost]";
        cost.placeholder = "0"
        cost.classList.add('form-control');
        cost.classList.add('column');
        row3.appendChild(cost_label);
        row3.appendChild(cost);
        container.appendChild(row3);

        var row4 = document.createElement("div");
        row4.classList.add("row");
        var rarity_label = document.createElement("label");
        rarity_label.htmlFor = "items[][rarity]";
        rarity_label.innerHTML = "Rarity";
        rarity_label.classList.add('column');
        var rarity = document.createElement("select");
        rarity.required = true;
        rarity.name = "items[][rarity]";
        rarity.id = "items[][rarity]";
        rarity.classList.add('form-control');
        rarity.classList.add('column')
        row4.appendChild(rarity_label)
        row4.appendChild(rarity);
        var common = document.createElement("option")
        common.value = "0";
        common.innerHTML = "Common";
        rarity.appendChild(common);
        var uncommon = document.createElement("option")
        uncommon.value = "1";
        uncommon.innerHTML = "Uncommon";
        rarity.appendChild(uncommon);
        var rare = document.createElement("option")
        rare.value = "2";
        rare.innerHTML = "Rare";
        rarity.appendChild(rare);
        container.appendChild(row4);
        container.appendChild(document.createElement("br"))

    }
}