function httpGet(theUrl)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", theUrl, false ); // false for synchronous request
    xmlHttp.send(null);
    return xmlHttp.responseText;
}

function processForm(e) {
    if (e.preventDefault) e.preventDefault();
    addr = document.getElementById("address").value;
    console.log(
      httpGet("http://localhost:5000/?address=" + encodeURIComponent(addr))
    );

    // Return false to prevent the default form behavior
    return false;
}

var form = document.getElementById('geocode-form');
if (form.attachEvent) {
    form.attachEvent("submit", processForm);
} else {
    form.addEventListener("submit", processForm);
}
