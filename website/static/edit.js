window.onload = function() {
    showDanger();
};

function showDanger() {
    if (document.getElementById("show_danger").checked) {
        $(".danger").show();
    }
    else {
        $(".danger").hide();
    }
}