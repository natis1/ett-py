function addItems(){
    var placeholders = ["Boots of Bouncing (Greater)", "Unstoppable Rod", "Immovable Object",
    "Steam Deck of Many Things", "Kemono Mask", "Wonderless Figurine (Orange Hyena)", "Eldest Seed",
    "Triangular Sawtooth", "Enveloping Blight", "Aeon Stone (Puke Green)", "Bread Ampule (Lesser)",
    "Mary Jane", "Uranium-235", "Critical Fumble Deck", "Pocket Mansion",
    "Smartphone", "Circus in a Box", "The Game Mastery's Guide", "Curse of the First Dragon",
    "Ant"];
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
        row1.classList.add("ettrow");
        row1.classList.add("required");
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
        row2.classList.add("ettrow");
        row2.classList.add("required");
        var level_label = document.createElement("label");
        level_label.htmlFor = "items[][level]";
        level_label.innerHTML = "Level:";
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

        var row4 = document.createElement("div");
        row4.classList.add("ettrow");
        row4.classList.add("required");
        var rarity_label = document.createElement("label");
        rarity_label.htmlFor = "items[][rarity]";
        rarity_label.innerHTML = "Rarity:";
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

function addPlayers(characters) {
    var number = document.getElementById("playersNr").value;
    if (number > 8) {
        number = 8;
    }
    var default_time = document.getElementById("time").value;
    var container = document.getElementById("player-container");
    while (container.hasChildNodes()) {
        container.removeChild(container.lastChild);
    }

    for (i=0; i<number; i++){
        var row1 = document.createElement("div");
        row1.classList.add("ettrow");
        row1.classList.add("required");
        var name_label = document.createElement("label");
        name_label.htmlFor = "players[][name]";
        name_label.innerHTML = "Player " + (i+1) + ":";
        name_label.classList.add('column');
        var name = document.createElement("select");
        name.name = "players[][name]";
        name.id = "players[][name]";
        name.classList.add('form-control');
        name.classList.add('column');
        for (j=0; j < characters.length; j++) {

            var option = document.createElement("option");
            option.innerHTML = characters[j][0] + " -> " + characters[j][1];
            option.value = characters[j][0] + "|" + characters[j][1];
            name.appendChild(option);
        }
        row1.appendChild(name_label);
        row1.appendChild(name);
        container.appendChild(row1);

        var row2 = document.createElement("div");
        row2.classList.add("ettrow");
        row2.classList.add("required");
        var level_label = document.createElement("label");
        level_label.htmlFor = "players[][level]";
        level_label.innerHTML = "Level: ";
        level_label.classList.add('column');
        var level = document.createElement("input");
        level.required = true;
        level.type = "number";
        level.step = "1";
        level.min = "1";
        level.max = "20";
        level.name = "players[][level]";
        level.id = "players[][level]";
        level.classList.add('form-control');
        level.classList.add('column');
        row2.appendChild(level_label);
        row2.appendChild(level);
        container.appendChild(row2);

        var row3 = document.createElement("div");
        row3.classList.add("ettrow");
        var time_label = document.createElement("label");
        time_label.htmlFor = "players[][time]";
        time_label.innerHTML = "Time Played: ";
        time_label.classList.add('column');
        var time = document.createElement("input");
        time.required = true;
        time.type = "number";
        time.step = "0.01";
        time.min = "0";
        time.max = "100";
        time.name = "players[][time]";
        time.id = "players[][time]";
        time.value = default_time;
        time.classList.add('form-control');
        time.classList.add('column');
        row3.appendChild(time_label);
        row3.appendChild(time);
        container.appendChild(row3);

        var row4 = document.createElement("div");
        row4.classList.add("ettrow");
        var minirow3 = document.createElement("div");
        minirow3.classList.add("column");
        minirow3.classList.add("halfrow");
        var minirow4 = document.createElement("div");
        minirow4.classList.add("column");
        var karma_label = document.createElement("label");
        karma_label.htmlFor = "players[][karma]";
        karma_label.innerHTML = "Karma Gained: ";
        karma_label.classList.add('column');
        // Hacky ass shit to let us use checkboxes here
        var karma_hidden = document.createElement("input");
        karma_hidden.type = "hidden";
        karma_hidden.name = "players[][karma]";
        karma_hidden.value = "0";
        var karma = document.createElement("input");
        karma.type = "checkbox";
        karma.name = "players[][karma]";
        karma.id = "players[][karma]";
        karma.value = "1";
        karma.classList.add('form-control');
        karma.classList.add('column');
        minirow3.appendChild(karma_label);
        minirow3.appendChild(karma);
        minirow3.appendChild(karma_hidden);
        row4.appendChild(minirow3);
        row4.appendChild(minirow4);
        container.appendChild(row4);

        var row5 = document.createElement("div");
        row5.classList.add("ettrow");
        var minirow1 = document.createElement("div");
        minirow1.classList.add("column");
        minirow1.classList.add("halfrow");
        tt_label = document.createElement("label");
        tt_label.innerHTML = "TT Karma:";
        tt_label.classList.add('column');
        // Hacky ass shit to let us use checkboxes here
        var tt_hidden = document.createElement("input");
        tt_hidden.type = "hidden";
        tt_hidden.name = "players[][ttcost]";
        tt_hidden.value = "0";
        var tt_cost = document.createElement("input");
        tt_cost.type = "checkbox";
        tt_cost.value="1";
        tt_cost.classList.add('column');
        tt_cost.name = "players[][ttcost]";
        minirow1.appendChild(tt_label);
        minirow1.appendChild(tt_cost);
        minirow1.appendChild(tt_hidden);
        var minirow2 = document.createElement("div");
        minirow2.classList.add("column");
        minirow2.classList.add("halfrow");
        minirow2.classList.add("custom-checkbox");
        die_label = document.createElement("label");
        die_label.innerHTML = "Died:";
        die_label.classList.add('column');
        // Hacky ass shit to let us use checkboxes here
        var die_hidden = document.createElement("input");
        die_hidden.type = "hidden";
        die_hidden.name = "players[][died]";
        die_hidden.value = "0";
        var did_die = document.createElement("input");
        did_die.type = "checkbox";
        did_die.value = "1";
        did_die.name = "players[][died]";
        did_die.id = "players[][died]";
        did_die.classList.add('column');

        did_die.classList.add('cb-danger');
        minirow2.appendChild(die_label);
        minirow2.appendChild(did_die);
        minirow2.appendChild(die_hidden);
        row5.appendChild(minirow1);
        row5.appendChild(minirow2);
        container.appendChild(row5);
        var br = document.createElement("br");
        container.appendChild(br);
    }
}

async function DryRun() {
    var form = new FormData(document.getElementById("form"));
    console.log(form);
    const response = await fetch('/add_adventure', {
        "method": "POST",
        "body": form
    });
    const jsonData = await response.json();
    output = document.getElementById("dryresults");
    while (output.hasChildNodes()) {
        output.removeChild(output.lastChild);
    }
    for (i=0; i < jsonData.length; i++) {
        var cur = jsonData[i];
        console.log(cur);
        var label = document.createElement("label");
        // You are the GM
        if (cur.name == "GM" && form.gm == cur.player_name) {
            label.innerHTML = "GM (" + form.gm + ") will gain: " + cur.xp_change.toFixed(2) + " XP" + " and " + cur.karma_change + " karma.";
        } else {
            label.innerHTML = "Player: " + cur.player_name + " will gain " + cur.karma_change + " karma and PC: " + cur.name + " will gain: " +
                              cur.xp_change.toFixed(2) + " XP. Community service hours changes by: " + cur.cs_change + ". Listed items will be unlocked: ";
            if (!!cur.items){
                for (const j of cur.items) {
                    label.innerHTML += j.name + ", ";
                }
            }
        }
        output.appendChild(label);
    }
    console.log(jsonData);

}