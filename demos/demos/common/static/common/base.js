// Set current locale ----------------------------------------------------------

moment.locale($("html").attr("lang"));

// ISO8601 to local date and time conversion -----------------------------------

$(".datetime-iso8601").each(function(index, element) {
	
	var element = $(element);
	var format = element.data("format");
	var datetime = moment(element.text());
	
	if (datetime.isValid()) {
		element.text(datetime.format(format));
	}
});

// Election ID input -----------------------------------------------------------

$(".election-id-input").click(function(e) {
	
	var modal = $("#election-id-modal");
	var input = modal.find("input");
	
	input.val("");
	input.trigger("change");
	input.data("href", $(this).attr("href"));
	
	modal.find(".modal-title").text($(this).html().replace(/<.*>/, ""));
	modal.modal("show");
	
	modal.on("shown.bs.modal", function(e) {
		input.focus();
	});
	
	return false;
});

$("#election-id-modal button:last").click(function(e) {
	
	var modal = $("#election-id-modal");
	var input = modal.find("input");
	
	var value = input.val();
	
	if (!value) {
		input.parent(".form-group").addClass("has-warning has-feedback");
		input.siblings(".form-control-feedback").removeClass("hidden");
		input.css("text-indent", "30px");
		input.focus();
	}
	else {
		modal.find("button").add(input).prop("disabled", true);
		modal.find(".progress").closest(".row").removeClass("hidden");
		window.location.href = input.data("href") + value.toUpperCase() + "/";
	}
});

$("#election-id-modal input").on("input change", function(e) {
	
	var input = $(this);
	
	input.parent(".form-group").removeClass("has-warning has-feedback");
	input.siblings(".form-control-feedback").addClass("hidden");
	input.css("text-indent", "0px");
});

$("#election-id-modal input").keypress(function(e) {
	
	if (e.which == 13) {
		$("#election-id-modal button:last").click();
	}
});

// Election box ----------------------------------------------------------------

$(".election-box > .header > span > span:not(.glyphicon)").each(function(index, element) {
	
	var span = $(element);
	
	var t1 = moment(span.data("t1"));
	var t2 = moment(span.data("t2"));
	
	span.text(span.text().replace("%s", t1.to(t2, true)));
});

// Numeric input in textbox ----------------------------------------------------

$(".input-type-number").on("change update", function(e) {
	
	var input = $(this);
	
	var new_value = input.val();
	var value = input.data("value") || "";
	
	var min_value = parseInt(input.prop("min"));
	var max_value = parseInt(input.prop("max"));
	
	// Restore old value if new value is not a number or out of range
	
	if (new_value && /^\d*$/.test(new_value)) {
		
		new_value = parseInt(new_value);
		
		if ((!min_value || new_value >= min_value)
		&& (!max_value || new_value <= max_value))
			value = new_value;
	}
	else if (!new_value) value = "";
	
	input.val(value);
	input.data("value", value);
});

$(".number-input").trigger("change");

// Select placeholder ----------------------------------------------------------

$(".select-placeholder").on("change update", function(e) {
	
	var color = $(this).children("option:first-child").is(":selected") ? "#999" : "#555";
	$(this).css("color", color);
	
}).trigger("change");

// Pad a numeric string on the left with zero digits ---------------------------

function zfill(num, width) {
	
	var val = Math.abs(num);
	var sign = (num < 0) ? "-" : "";
	
	var zeros_count = Math.max(0, width - Math.floor(val).toString().length);
	var zeros = Array(zeros_count + 1).join("0");
	
	return sign + zeros + val;
}

// Parse cookie, CSRF token value ----------------------------------------------

function getCookie(name) {
	
	// https://docs.djangoproject.com/en/1.8/ref/csrf/#ajax
	
	var cookieValue = null;
	if (document.cookie && document.cookie != "") {
		var cookies = document.cookie.split(";");
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) == (name + "=")) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

var csrfmiddlewaretoken = getCookie("csrftoken");

// Default spinner options -----------------------------------------------------

var def_spinner_opts = {
	lines: 13, // The number of lines to draw
	length: 28, // The length of each line
	width: 14, // The line thickness
	radius: 42, // The radius of the inner circle
	scale: 1, // Scales overall size of the spinner
	corners: 1, // Corner roundness (0..1)
	color: '#000', // #rgb or #rrggbb or array of colors
	opacity: 0.25, // Opacity of the lines
	rotate: 0, // The rotation offset
	direction: 1, // 1: clockwise, -1: counterclockwise
	speed: 1, // Rounds per second
	trail: 60, // Afterglow percentage
	fps: 20, // Frames per second when using setTimeout() as a fallback for CSS
	zIndex: 2e9, // The z-index (defaults to 2000000000)
	className: 'spinner', // The CSS class to assign to the spinner
	top: '50%', // Top position relative to parent
	left: '50%', // Left position relative to parent
	shadow: false, // Whether to render a shadow
	hwaccel: false, // Whether to use hardware acceleration
	position: 'absolute', // Element positioning
}
