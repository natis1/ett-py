window.onload = function() {
    var container = document.getElementById("sendto");

    for (i=0; i<chars.length; i++){
        var option = document.createElement("option");
        option.innerHTML = chars[i][0] + " -> " + chars[i][1];
        option.value = chars[i][0] + "|" + chars[i][1];
        container.appendChild(option);
    }
}