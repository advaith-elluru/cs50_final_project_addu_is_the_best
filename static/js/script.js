function choose()
{
    var x = document.getElementById("choice");
    var y = document.getElementById("amount");
    if (x.options[x.selectedIndex].value === "best_percentage" || x.options[x.selectedIndex].value === "best_time")
    {
        y.style.display = "block";
    }
}

function test()
{
    $("#table tr").each(function() {
        
    });
}

document.addEventListener("DOMContentLoaded", function () {

})