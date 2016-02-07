$("#id_ballots").slider();
$("#id_ballots").on("slide", function(slideEvt) {
	$("#ex6SliderVal").text(slideEvt.value);
});
