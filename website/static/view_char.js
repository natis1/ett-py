function download(url) {
    var file_path = url;
    var a = document.createElement('A');
    a.href = file_path;
    a.download = file_path.substr(file_path.lastIndexOf('/') + 1);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

window.onload = function() {
    var fvtt_container = document.getElementById("fvtt-container");
    var pdf_container = document.getElementById("pdf-container");
    var row1 = document.createElement("div");
    row1.classList.add("ettrow");
    var row2 = document.createElement("div");
    row2.classList.add("ettrow");
    var row3 = document.createElement("div");
    row3.classList.add("ettrow");
    var row4 = document.createElement("div");
    row4.classList.add("ettrow");

    for (let i = 0; i < 20; i++){
        var button_div = document.createElement("div");
        button_div.style.cssText += 'flex:10%;'
        var button = document.createElement("button");
        button.type = "button";
        button.classList.add('btn');
        button.innerHTML = (i + 1);
        if (fvtts[i] == '') {
            button.classList.add('btn-danger');
        } else {
            button.setAttribute('onclick', "download('" + fvtts[i] + "')");
            button.classList.add('btn-primary');
        }
        button_div.appendChild(button);
        if (i < 10){
            row1.appendChild(button_div);
        }
        else {
            row2.appendChild(button_div);
        }
    }

    for (let i = 0; i < 20; i++){
        var button_div = document.createElement("div");
        button_div.style.cssText += 'flex:10%;'
        var button = document.createElement("button");
        button.type = "button";
        button.classList.add('btn');
        button.innerHTML = (i + 1);
        if (pdfs[i] == '') {
            button.classList.add('btn-danger');
        } else {
            button.setAttribute('onclick', "download('" + pdfs[i] + "')");
            button.classList.add('btn-primary');
        }
        button_div.appendChild(button);
        if (i < 10){
            row3.appendChild(button_div);
        }
        else {
            row4.appendChild(button_div);
        }
    }
    fvtt_container.appendChild(row1);
    fvtt_container.appendChild(row2);
    pdf_container.appendChild(row3);
    pdf_container.appendChild(row4);
};