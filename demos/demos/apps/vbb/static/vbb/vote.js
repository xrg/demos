$(window).load(function() {
	carousel_upd_all();
});

$(document).ready(function() {
	$(".alert-warning").addClass("hidden");
});

// -----------------------------------------------------------------------------

// Prepare carousel

var carousel = $("#carousel").carousel();

carousel.swipeleft(function() {  
	$(this).carousel("next");
});

carousel.swiperight(function() {  
	$(this).carousel("prev");
});

if (!carousel.data("wrap"))
	carousel.find(".carousel-control.left").addClass("disabled");

// -----------------------------------------------------------------------------

$(".page-header a").click(function(e) {
	$(this).toggleClass("active");
});

$("#vote-submit").tooltip({
	trigger: "manual",
	container: "body",
	placement: function() {
		switch ($("#vote-submit").parent().css("text-align")) {
			case "center": return "top";
			case "right": return "left";
			case "left": return "right";
			default: return "auto";
		}
	},
});

// -----------------------------------------------------------------------------

function ajax_error_msg(jqXHR, modal) {
	
	// Determine proper error state
	
	var state;
	
	if (jqXHR.status == 0)
		state = State.CONNECTION_ERROR;
	else if (!jqXHR.hasOwnProperty("responseJSON") || jqXHR.responseJSON.hasOwnProperty("error"))
		state = State.SERVER_ERROR;
	else
		state = jqXHR.responseJSON.error;
	
	// Disable all options
	
	disable_vote_ui();
	
	// Display an alert with the the error message
	
	var alert_danger = $(".alert-danger");
	
	alert_danger.removeClass("hidden");
	alert_danger.find("span[data-state='" + state + "']").removeClass("hidden");
	alert_danger.find("span:not([data-state='" + state + "'])").addClass("hidden");
	
	// Scroll to the alert element
	
	if (typeof modal !== "undefined")
		modal.modal("hide");
	
	$("html, body").animate({
		scrollTop: $("main").offset().top
	}, 400);
}

function disable_vote_ui() {
	
	var carousel = $("#carousel");
	var submit_btn = $("#vote-submit");
	var options = carousel.find("button.active");
	
	carousel.addClass("disabled");
	carousel.find("button").prop("disabled", true);
	
	options.removeClass("active");
	options.attr("aria-pressed", false);
	options.find(".glyphicon").addClass("hidden");
	
	submit_btn.prop("disabled", true);
}

// -----------------------------------------------------------------------------

$(".option").click(function(e) {
	
	var option = $(this);
	var index = option.data("index");
	var selected = !option.hasClass("active");
	
	option.toggleClass("active");
	option.attr("aria-pressed", selected);
	option.find(".glyphicon").toggleClass("hidden", !selected);
	
	var question = option.closest(".question");
	var checked_queue = question.data("checked-queue");
	
	if (selected) {
		
		var max_choices = question.data("max-choices");
		var choices = question.find(".option.active").not(this).length;
		
		if (choices >= max_choices) {
			
			var last_index = checked_queue.shift();
			var last_selected = question.find(".option[data-index='" + last_index + "']");
			
			last_selected.removeClass("active");
			last_selected.attr("aria-pressed", false);
			last_selected.find(".glyphicon").addClass("hidden");
		}
		
		if (typeof checked_queue === "undefined") {
			
			checked_queue = new Array();
			question.data("checked-queue", checked_queue);
		}
		
		checked_queue.push(index);
	
	} else {
		
		var pos = checked_queue.indexOf(index);
		checked_queue.splice(pos, 1);
	}
});

// -----------------------------------------------------------------------------

$("#security-code-input").on("input", function(e) {
	
	var input = $(this);
	var value = input.val();
	var maxlen = input.prop("maxLength");
	
	if (value.length != maxlen) {
		security_code_state("reset");
		return;
	}
	
	security_code_state("spin");
	
	var salt = input.data("salt");
	var iterations = input.data("iterations");
	
	value = sjcl.codec.base32.normalize(value);
	
	var hash_value = sjcl.codec.base64.fromBits(
		sjcl.misc.pbkdf2(value, salt, iterations)
	);
	
	$.ajax({
		type: "POST",
		data: {
			csrfmiddlewaretoken: csrfmiddlewaretoken,
			jsonfield: JSON.stringify({command: 'security-code', hash_value: hash_value}),
		},
		success: function(data, textStatus, jqXHR) {
			
			var votecodes = data;
			
			var base32 = input.val();
			var bits = sjcl.codec.base32.toBits(base32);
			
			$(".question").each(function(index, question) {
				
				var index = $(question).data("index");
				
				var number = sjcl.bn.fromBits(bits).add(index).toBits();
				var hash = sjcl.hash.sha256.hash(number);
				var perm = sjcl.bn.fromBits(hash);
				
				var votecode_list = permute_ori(votecodes[index], perm);
				
				$(question).find(".option").each(function(index, option) {
					var index = $(option).data("index");
					$(option).data("votecode", votecode_list[index]);
				});
			});
			
			security_code_state("success");
			$("#security-code-info").text(base32);
		},
		error: function(jqXHR, textStatus, errorThrown) {
			
			if (jqXHR.status == 403) {
				
				security_code_state("error");
				input.focus();
				
			} else {
				
				ajax_error_msg(jqXHR, $("#security-code-modal"));
			}
		},
	});
});

$("#security-code-cancel").click(function(e) {
});

function security_code_state(state) {
	
	var input = $("#security-code-input");
	var btn_ok = $("#security-code-ok");
	
	var form_group = input.closest(".form-group");
	var form_control = input.siblings(".form-control-feedback");
	
	form_group.removeClass("has-feedback has-success has-error");
	form_control.removeClass("glyphicon-ok glyphicon-remove glyphicon-refresh glyphicon-spin hidden");
	
	if (state == "success") {
		
		form_group.addClass("has-feedback has-success");
		form_control.addClass("glyphicon-ok");
		
		btn_ok.prop("disabled", false);
		input.prop("disabled", true);
		
		input.css("text-indent", "30px");
		btn_ok.focus();
		
	} else if (state == "error") {
		
		form_group.addClass("has-feedback has-error");
		form_control.addClass("glyphicon-remove");
		
		btn_ok.prop("disabled", true);
		input.prop("disabled", false);
		
		input.css("text-indent", "30px");
		
	} else if (state == "spin") {
		
		form_group.addClass("has-feedback");
		form_control.addClass("glyphicon-refresh glyphicon-spin");
		
		btn_ok.prop("disabled", true);
		input.prop("disabled", true);
		
		input.css("text-indent", "30px");
		
	} else if (state == "reset")  {
		
		form_control.addClass("hidden");
		
		btn_ok.prop("disabled", true);
		input.prop("disabled", false);
		
		input.css("text-indent", "0px");
	}
}

// -----------------------------------------------------------------------------

$("#vote-submit").click(function(e) {
	
	var questions = $(".question");
	
	// Check if the user has voted for all questions
	
	var filled_questions = 0;
	
	questions.each(function(index, element) {
		
		var question = $(element);
		
		if (question.find(".option.active").length > 0) 
			filled_questions += 1;
	});
	
	if (filled_questions < questions.length) {
		
		// Not all questions have been filled in. Animate carousel's control
		// buttons to attract the user's attention and popup a tooltip.
		
		var controls = $(".carousel-control");
		controls.addClass("transform");
		
		window.setTimeout(function() {
			controls.removeClass("transform");
		}, 1500);
		
		$(this).tooltip("show");
		return;
	}
	
	// Now, fill in the confirm-modal with the user's selections
	
	var confirm_modal = $("#confirm-modal");
	
	modal_with_tables(confirm_modal, questions, function(question, table) {
		
		var vc_chars = ((question.find(".option").length - 1) + "").length;
		
		question.find(".option.active").each(function(index, element) {
			
			var option = $(element);
			var text = option.text();
			var votecode = option.data("votecode");
			
			table.append("<tr><td>" + text + "</td><td>" + zfill(votecode, vc_chars) + "</td></tr>");
		});
	});
	
	confirm_modal.modal("show");
});

$("#vote-submit").focusout(function(e) {
	$(this).tooltip("hide");
});

$("#vote-confirm").click(function(e) {
	
	$(this).siblings().addBack().prop("disabled", true);
	
	// Prepare the data for the server. 'votecodes' is an array of questions,
	// ordered by their index. Each array's element is another array of the
	// selected votecodes.
	
	var questions = $(".question");
	var votecodes = new Array();
	
	questions.each(function(index, element) {
		
		var question = $(element);
		var index = question.data("index");
		
		var votecode_list = new Array();
		
		question.find(".option.active").each(function(index, element) {
			
			var option = $(element);
			var votecode = option.data("votecode");
			
			votecode_list.push(votecode);
		});
		
		votecodes[index] = votecode_list;
	});
	
	// Now, send the votecodes to the server
	
	$.ajax({
		type: "POST",
		data: {
			csrfmiddlewaretoken: csrfmiddlewaretoken,
			jsonfield: JSON.stringify({command: 'vote', votecodes: votecodes}),
		},
		success: function(data, textStatus, jqXHR) {
			
			// Fill in the receipt-modal with the received receipts
			
			var receipt_modal = $("#receipt-modal");
			var confirm_modal = $("#confirm-modal");
			
			modal_with_tables(receipt_modal, questions, function(question, table) {
				
				question.find(".option.active").each(function(index, element) {
					
					var option = $(element);
					
					var text = option.text();
					var votecode = option.data("votecode");
					var receipt = data[question.data("index")].shift();
					
					table.append("<tr><td>" + text + "</td><td>" + votecode + "</td><td>" + receipt + "</td></tr>");
				});
			});
			
			disable_vote_ui();
			confirm_modal.modal("hide");
			
			confirm_modal.on("hidden.bs.modal", function (e) {
				receipt_modal.modal("show");
			});
		},
		error: function(jqXHR, textStatus, errorThrown) {
			
			ajax_error_msg(jqXHR, $("#confirm-modal"));
		},
	});
});

function modal_with_tables(modal, questions, callback) {
	
	var base_panel = modal.find(".panel.hidden");
	modal.find(".panel:not(.hidden)").remove();
	
	questions.each(function(index, element) {
		
		var question = $(element);
		var panel = base_panel.clone();
		
		panel.removeClass("hidden");
		panel.insertBefore(base_panel);
		
		var table = panel.find("table > tbody");
		var heading = panel.find(".panel-heading");
		
		var index = question.data("index");
		var title = question.find(".title").text();
		
		heading.append(((questions.length > 1) ? (" " + (index + 1)) : ("")) + ": " + title);
		return callback(question, table);
	});
}

$("#receipt-modal .modal-header .close").click(function(e) {
	
	$("#receipt-modal").modal("hide");
	$(".alert-success").removeClass("hidden");
	
	$("html, body").animate({
		scrollTop: $("main").offset().top
	}, 400);
});

// -----------------------------------------------------------------------------

$("#carousel").on("slide.bs.carousel", function(e) {
	
	var carousel = $(this);
	var item = $(e.relatedTarget);
	
	// Update controls for the new item
	
	var active = item.hasClass("active");
	
	item.addClass("active");
	carousel_upd_controls(item);
	
	if (!active);
		item.removeClass("active");
	
	// Animate the carousel
	
	carousel.find(".carousel-inner").animate({height: item.outerHeight()}, 500);
	
	// Enable/disable controls if on the first/last item
	
	if (!carousel.data("wrap")) {
		
		var control_left = carousel.find(".carousel-control.left");
		var control_right = carousel.find(".carousel-control.right");
		
		if(e.direction == "right" && $(e.relatedTarget).is(":nth-child(1)")) {
			control_left.addClass("disabled");
		} else if (e.direction == "left" && !$(e.relatedTarget).is(":nth-child(1)")) {
			control_left.removeClass("disabled");   
		}
		
		if (e.direction == "left" && $(e.relatedTarget).is(":nth-last-child(1)")) {
			control_right.addClass("disabled");
		} else if (e.direction == "right" && !$(e.relatedTarget).is(":nth-last-child(1)")) {
			control_right.removeClass("disabled");      
		}
	}
});

function carousel_upd_header(item) {
	
	var carousel = $("#carousel");
	var item = item || carousel.find(".item.active");
	
	// Calculate title span's width, needed by the flexbox for centering
	
	var h3 = item.find(".page-header > h3");
	var span = h3.children("span");
	
	h3.css("display", "inline");
	span.css("width", "");
	
	var width = span.width();
	
	h3.css("display", "");
	span.css("width", width);
}

function carousel_upd_controls(item) {
	
	var carousel = $("#carousel");
	var item = item || carousel.find(".item.active");
	var header = item.find(".page-header");
	
	carousel.find(".carousel-inner").css("height", "auto");
	
	var controls = carousel.find(".carousel-control");
	var min_width_768px = (parseInt($("#media-query-test").css("min-width")) >= 768);
	
	var width = min_width_768px ? item.css("padding-left") : (item.outerWidth() - header.width()) / 2;
	var height = min_width_768px ? "100%" : header.outerHeight() + parseInt(header.css("margin-top"));
	
	controls.css({"width": width, "height": height});
	controls.find(".glyphicon").css("top", "50%");
}

function carousel_upd_all() {
	
	$("#carousel .item").each(function(index, element) {
		
		var item = $(element);
		var active = item.hasClass("active");
		
		item.addClass("active");
		
		carousel_upd_header(item);
		
		if (!active)
			item.removeClass("active");
	});
	
	carousel_upd_controls();
}

var debounce = function (func, threshold, execAsap) {
	
	// http://www.paulirish.com/2009/throttled-smartresize-jquery-event-handler/
	// http://unscriptable.com/index.php/2009/03/20/debouncing-javascript-methods/
	
	var timeout;
	
	return function debounced () {
		var obj = this;
		function delayed () {
			if (!execAsap)
				func.apply(obj);
			timeout = null;
		};
		
		if (timeout)
			clearTimeout(timeout);
		else if (execAsap)
			func.apply(obj);
		
		timeout = setTimeout(delayed, threshold || 100);
	};
}

$(window).resize(debounce(carousel_upd_all));

// -----------------------------------------------------------------------------

// Factorial, n-th permutation and original from n-th permutation functions.
// A sjcl version with division support is required.

function factorial(n) {
	
	var n = new sjcl.bn(n);
	var i = new sjcl.bn(2);
	var val = new sjcl.bn(1);
	
	while(n.greaterEquals(i)) {
		val = val.mul(i);
		i.addM(1);
	}
	
	return val;
}

function permute(iterable, index) {
	
	var seq = iterable.slice();
	var fact = factorial(seq.length);
	var index = (new sjcl.bn(index)).mod(fact);
	var perm = new Array();
	var divmod;
	
	while (seq.length > 0) {
		
		fact = fact.div(seq.length);
		divmod = index.divmod(fact);
		next = divmod[0];
		index = divmod[1];
		item = seq.splice(parseInt(next.toString(), 16), 1);
		perm.push(item);
	}
	
	return perm;
}

function permute_ori(iterable, index) {
	
	var seq = iterable.slice();
	
	var fact = factorial(seq.length);
	var index = (new sjcl.bn(index)).mod(fact);
	
	var divmod;
	var next = new Array();
	
	for (var i = seq.length; i > 0; i--) {
		
		fact = fact.div(i);
		
		divmod = index.divmod(fact);
		pos = divmod[0];
		index = divmod[1];
		
		next.push(pos);
	}
	
	var pos, item;
	var perm = new Array();
	
	for (var i = seq.length - 1; i >= 0; i--) {
		pos = next[i];
		item = seq[i];
		perm.splice(pos, 0, item)
	}
	
	return perm;
}

