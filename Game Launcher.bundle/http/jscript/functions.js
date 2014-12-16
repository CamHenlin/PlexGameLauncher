//Define some variables
var sections = []; // Holds all the available sections
var section_contents = []; // Holds the contents of the currently selected section.
var current_page = 0; // Always default to 0

var presentable_contents = []; // Holds the contents after they have gone through the options-machine.
var searchstring = "";
var log = [];
var log_show_amount = 5;
var selected_section = 0;

var trigger = "";
var library = "";

// Not yet implemented. To be used in error: in ajax calls
function error_ajax_calls() { }

// This is the initial function. This is called upon page loading to populate the sections table with the available sections.
function fetch_sections() {
	start_timer();
	$("#LibraryBox table").html(loadingScreen);
	$("input[name=items_per_page]").val(items_per_page);
	$.ajax({
		type: "GET",
		url: baseurl + utility + "/allconsoles?title=",
		dataType: "xml",
		global: false,
		//cache: false,
		success: function(data) {
			
			$("#LibraryBox table").html("");
			$(data).find("Directory").each(function() {
				
				targetFunction = "fetch_console";
				
				$("#LibraryBox table").append("<tr class='hovering'><td class='mainText'><span class='link' onclick='function_loader(\"" + targetFunction + "\",[\"" + $(this).attr("key") + "\", this]);'>" + $(this).attr("title") + "</span></td><td class='mainText'><span class='link' onclick='remove_console(\""+ $(this).attr("title") +"\")'>Del</span></td></tr>");
				section = {
					key: $(this).attr("key"),
					title: $(this).attr("title"),
					refreshing: false
				};
				sections.push(section);
			});
			end_timer();
			log_add("Finished loading sections.");
		},
		error: function(data, status, statusText, responsText) {
			log_to_console(statusText);
		},
		complete: function(data, textStatus) {
			output_content(0);
		},
	});
}

function fetch_console(LibraryKey, TriggeringElement) {
	start_timer();
	//fetchSettings();
	reset_variables();
	current_section = get_section_info(LibraryKey);
	refresh_section_list(current_section.key, TriggeringElement);
	trigger = TriggeringElement;
	if (library != LibraryKey) {
		current_page = 0
	}
	library = LibraryKey;

	$.ajax({
		type: "GET",
		async: true,
		url: LibraryKey,
		dataType: "xml",
		//cache: false,
		success: function(data) {
			//xmlString = (new XMLSerializer()).serializeToString(data);
			//log_to_console(xmlString);

			consol = $(data).find("MediaContainer").attr("title2");

			$(data).find("Directory").each(function() {
				// For each item in the section, call the key+"/tree"
				item = new Video();
				item.title = $(this).attr("title");
				item.key = $(this).attr("key");
				item.summary = $(this).attr("summary");
				item.thumb = $(this).attr("thumb");
				item.id = $(this).attr("duration");
				item.type = 'game';
				item.console = consol
				section_contents.push(item);
			});
			//alert(section_contents[0])
		},
		error: function(data, status, statusText, responsText) {
			log_to_console(statusText);
		},
		complete: function(data, textStatus) {
			output_content(current_page);
		},
	});
}

////////////////////////////////////////////////////////////////////////////
// Functions for outputs
////////////////////////////////////////////////////////////////////////////

function output_content(show_page) {
	$("#MainBox").html("");
	output_content_prepare();
	current_page = show_page;
	output_pages(show_page);
	start_value = show_page * items_per_page;
	end_value = (parseInt(start_value) + parseInt(items_per_page));
	if (end_value > presentable_contents.length) {
		end_value = presentable_contents.length;
	}

	//log_to_console("Start Value: " + start_value);
	//log_to_console("End Value: " + end_value);
	for (i = start_value; i < end_value; i++) {
		item = presentable_contents[i];
		if(item.hide === false) {
			newEntry = "";
			if (item.type == "game") {

				newEntry = "<div class='VideoBox'><a name='"+item.id+"'></a><div class='VideoHeadline'>" + item.title + "</div>";
				newEntry += "<div class='VideoSubtitle'>";
				newEntry += "<table class='Max' cellspacing=0 cellpadding=0><tr><td class='image mainText'>";
				if (item.thumb != undefined) {
					newEntry += "<img src='" + item.thumb + "' width='150'>";
				} else {
					item.thumb = ''
				}
				newEntry += "</td><td class='mainText'>";
				if (item.summary != undefined && item.summary != '') {
					newEntry += item.summary;
				} else {
					item.summary = '';
					newEntry += "No description available.";
				}
				newEntry += "</td></tr></table></div>";

				newEntry += "<div class='VideoBottom'><button class='btn btn-default btn-xs' onclick=\"edit_rom('"+item.id+"','"+library+"');\">Edit</button> <button class='btn btn-default btn-xs' onclick=\"remove_rom('"+item.id+"');\">Delete</button> </div></div>";
			}				
			$("#MainBox").append(newEntry);
		}
	}
	$("input[name=searchbutton]").removeAttr("disabled");
}

/**
	* This function is used to prepare the output with regards to the selected options.
	* This is ONLY things that affect paging
	* This is needed to be able to calculate the pages correctly while still having the original data available.
*/
function output_content_prepare() {	
	presentable_contents = [];
	
	//console.log("Length of section_contents: " + section_contents.length);	
	for (i=0; i<section_contents.length;i++) {
		item = section_contents[i];
		discovered_languages = [];
		
		// Asume everything can be added.
		item.hide = false;
		
		log_to_console("Item Hide: " + item.hide);
		
		// If there is no searchstring, continue
		// log_to_console("Searchstring value: " + searchstring.toLowerCase());
		if(searchstring.length > 2) {
			log_to_console(item.title.toLowerCase().indexOf(searchstring.toLowerCase()));
			// If the searchstring is not found, then do not add it.
			if(item.title.toLowerCase().indexOf(searchstring.toLowerCase()) == -1) {
				item.hide = true;
			}
		}
		
		// If we are alowed to add it, do so.
		if(item.hide === false) {
			//log_to_console("Adding item in presentable_contents: " + item.title);
			presentable_contents.push(item);
		}
	}
	//log_to_console("length of presentable_contents: " + presentable_contents.length);
}

/**
	* This function counts the items to be displayed and shows any pagin if needed.
*/
function output_pages(show_page) {
	$("#PageBar").html("Game Launcher");
	var numberOfPages = presentable_contents.length / items_per_page;
	var pages = "Game Launcher";
	if (numberOfPages > 1) {
		pages = pages + "\t<ul class='pagination pagination-sm'>";
		
		for (i = 0; i < numberOfPages; i++) {
			if (i == show_page) {
				pages = pages + "<li class='active'> <span onclick='output_content(" + i + ");'>" + (i + 1) + "</span></li>";
				} else {
				pages = pages + "<li> <span onclick='output_content(" + i + ");'>" + (i + 1) + "</span></li>";
			}
			
		}
		pages = pages + "</ul>";
	}
	$("#PageBar").html(pages);
	//alert("Current Page: " + $("#PageBar .active span").html());
}

/**
	* This is to replace fetchSettings() and every other function call. Forcing update of settings before any call can be made.
*/
function function_loader(function_name,function_args) {
	// First of all, update the settings.
	$.ajax({
		url: baseurl + utility,
		cache: false,
		dataType: "xml",
		global: false,
		success: function(data) {
			$.ajax({
				url: "jscript/settings.js",
				cache: false,
				dataType: "script",
				global: false,
				success: function(data) {
					var perLine=data.split('\n');
					var myVars=[];
					for(i=0;i<perLine.length;i++)
					{
						var line=perLine[i].split(' ');
						myVars[i]={
							'variablename':line[1],
							'variablevalue':line[3]
						}
					}
					
					for(i=0;i<myVars.length;i++) {
						if(myVars[i].variablename !== undefined) {
							if( (myVars[i].variablename == "Secret") || (myVars[i].variablename == "PMSUrl") || (myVars[i].variablename == "options_hide_integrated") || (myVars[i].variablename == "options_hide_local") || (myVars[i].variablename == "options_hide_empty_subtitles") || (myVars[i].variablename == "options_only_multiple") || (myVars[i].variablename == "options_auto_select_duplicate") || (myVars[i].variablename == "items_per_page") ) {
								console.log("Updated setting " + myVars[i].variablename + " to value: " + myVars[i].variablevalue.substring(myVars[i].variablevalue.indexOf('"')+1,myVars[i].variablevalue.indexOf('";')));
								if(myVars[i].variablevalue.substring(myVars[i].variablevalue.indexOf('"')+1,myVars[i].variablevalue.indexOf('";')) == "true") {
									window[myVars[i].variablename] = true;						  
									} else if(myVars[i].variablevalue.substring(myVars[i].variablevalue.indexOf('"')+1,myVars[i].variablevalue.indexOf('";')) == "false") {
									window[myVars[i].variablename] = false;
									} else {
									window[myVars[i].variablename] = myVars[i].variablevalue.substring(myVars[i].variablevalue.indexOf('"')+1,myVars[i].variablevalue.indexOf('";'));		
								}
							}
						}
					}
					
					// Then call the function that is provided via function_name
					if(typeof(window[function_name]) == "function") {
						log_to_console("Calling function: " + function_name);
						window[function_name].apply(window,function_args);
						} else {
						log_to_console("Provided function_name is not a function: " + function_name);
					}
				},
				error: function(data) {
					log_to_console("An error has occurred in function_loader while fetching settings.js.");
				},
			});
		},
		error: function(data) {
			log_to_console("An error has occurred in function_loader while calling " + baseurl + utility);
		},
	});			
}

//////////////////////////////////////
// Generic functions
//////////////////////////////////////

// Returns the sectionobject for the requested one.
function get_section_info(LibraryKey) {
	for (i = 0; i < sections.length; i++) {
		if (sections[i].key == LibraryKey) {
			return sections[i];
		}
	}
}

function remove_console(title) {
	if (confirm('Are you sure you want to remove this console?')) {
		$.ajax({
			//http://192.168.1.10:32400/video/gamelauncher/delsysteminfo?console=AAE
			url: baseurl+utility+'/delsysteminfo?console='+title,
			dataType: "xml",
			global: false,
			//cache: false,
			success: function(data) {
				if ($(data).find("MediaContainer").attr("header") != 'Succes') {
					//alert('We had a problem removing the rom');
				}
				fetch_sections();
			},
			error: function(data) {
				log_to_console("An error has occurred while try to remove the rom.");
			}
		});
		return true;
	} else {
		return false;
	}
}

function remove_rom(id) {
	if (confirm('Are you sure you want to remove this rom?')) {
		$.ajax({
			url: baseurl+utility+'/delrominfo?id='+id,
			dataType: "xml",
			global: false,
			//cache: false,
			success: function(data) {
				if ($(data).find("MediaContainer").attr("header") != 'Succes') {
					//alert('We had a problem removing the rom');
				}
				fetch_console(library, trigger);
			},
			error: function(data) {
				log_to_console("An error has occurred while try to remove the rom.");
			}
		});
		return true;
	} else {
		return false;
	}
}

function edit_rom(id, library) {
	$.ajax({
		type: "GET",
		async: true,
		url: library,
		dataType: "xml",
		//cache: false,
		success: function(data1) {

			$(data1).find("Directory").each(function() {
				if (id == $(this).attr("duration")) {
					$("#id").val($(this).attr("duration"))

					$("#edit_title").val($(this).attr("title"));
					$("#edit_description").val($(this).attr("summary"));	
					$("#edit_boxart").val($(this).attr("thumb"));
					$("#EditBox").css("visibility","visible");		
				}
			});
		}
	});
}

function save_rom() {
	var data = {
		id: $("#id").val(),
	    title: $("#edit_title").val(),
	    description: $("#edit_description").val(),
	    url_boxart: $("#edit_boxart").val()
	}
	var json = JSON.stringify(data);

	$.ajax({
		type: "GET",
		async: true,
		url: baseurl + utility + '/saverom?json='+json,
		dataType: "xml",
		//cache: false,
		success: function(data1) {
			log_add("Succesfully updated the rom.");
		},
		error: function(data) {
			log_add("An error has occurred while trying to update the rom.");
		},
		complete: function(data, textStatus) {
			fetch_console(library, trigger);
			setTimeout(function() { scrollTo($("#id").val());},1000);
		},
	});
	$("#EditBox").css("visibility","hidden");
}

function scan_roms(section) {
	$("#ScanBox").css("visibility","visible");
	if (section == 'new') {
		time_out = (1000 * 60 * 60 * 24);
		$.ajax({
			url: baseurl+utility+'/:/function/RefreshDB',
			dataType: "xml",
			global: false,
			//cache: false,
			timeout: time_out,
			success: function(data) {
				if ($(data).find("MediaContainer").attr("header") != 'Succes') {
					alert('We had a problem removing the rom');
				}
			},
			error: function(data) {
				log_to_console("An error has occurred while try to remove the rom.");
			},
			complete: function(data, textStatus) {
				fetch_sections();
				$("#ScanBox").css("visibility","hidden");
			},
		});		
	} else if (section == 'metaunknown') {
		$.ajax({
			url: baseurl+utility+'/:/function/GetMissingInfo?query=unknown',
			dataType: "xml",
			global: false,
			//cache: false,
			timeout: time_out,
			success: function(data) {

			},
			error: function(data) {
				log_to_console("An error has occurred while try to remove the rom.");
			},
			complete: function(data, textStatus) {
				fetch_console(library, trigger);
				$("#ScanBox").css("visibility","hidden");
				setTimeout(function() { scrollTo($("#id").val());},1000);
			},
		});		
	} else if (section == 'metaknown') {
		$.ajax({
			url: baseurl+utility+'/:/function/GetMissingInfo',
			dataType: "xml",
			global: false,
			//cache: false,
			timeout: time_out,
			success: function(data) {

			},
			error: function(data) {
				log_to_console("An error has occurred while try to remove the rom.");
			},
			complete: function(data, textStatus) {
				fetch_console(library, trigger);
				$("#ScanBox").css("visibility","hidden");
				setTimeout(function() { scrollTo($("#id").val());},1000);
			},
		});		
	}
}

//////////////////////////////////////
// Functions for logs
//////////////////////////////////////

/**
	* This function adds the LogMessage to the Log array and correctly displays current information in the Log div, limited by log_show_amount
*/
function log_add(LogMessage) {
	
	$("#Log").html(""); 
	log.push(getDateTime() + " " + LogMessage);
	
	if(log.length>log_show_amount) {
		start = log.length - log_show_amount;
		} else {
		start = 0;
	}	
	
	$("#Log").append("<div class='VideoHeadline'>Log</div>");
	for (i=start;i<log.length;i++) {
		$("#Log").append("<div class='VideoSubtitle'>"+log[i]+"</div>");
	}
	$("#Log").append("<div class='VideoBottom'><button class='btn btn-default btn-xs' onclick='log_view()'>View complete log</button></div>");
}

function log_to_console(Message) {
	if ( (typeof(console) == "object") && ("console" in window) ) {
		
		try {
			console.log(Message);
		}
		catch (e) {}
		finally {
			return;
		}
	}
}

/**
	* This function displays the entire log generated through the current visit in a new window.
*/
function log_view() {
	var temporaryWindow = window.open('view_log.html');
	var content = "<div id='Log' class='VideoBox'><div class='VideoHeadline'>Log</div>";
	for (i=0;i<log.length;i++) {
		content += "<div class='VideoSubtitle'>"+log[i]+"</div>";
	}
	content += "</div>";
	setTimeout(function() {$(temporaryWindow.document.body).html(content);},1000);
}

////////////////////////////////////////////////////////////////////////////
// Functions for options
////////////////////////////////////////////////////////////////////////////
/**
	* This function takes the name of the option and it's value and sends it to the bundlepart. Saving it in settings.js for later.
*/
function options_save(option_name,option_value,number) {
	
	console.log("Saving Options for number: " + number);
	console.log("RequestedURL: " + baseurl + utility + "?Func=SetPref&Secret="+Secret+"&Pref="+option_name[number]+"&Value="+option_value[number]);
	$.ajax({
		type: "GET",
		url: baseurl + utility + "?Func=SetPref&Secret="+Secret+"&Pref="+option_name[number]+"&Value="+option_value[number],
		dataType: "text",
		cache: false,
		global: false,
		success: function(data) {
			console.log(data);
			if(data == "ok") {
				log_add("Successfully saved setting: ("+ number +")" + option_name[number] + " as: " + option_value[number]);
				} else {
				log_add("Failed saving setting: ("+ number +")" + option_name[number] + " as: " + option_value[number]);
			}
			var new_number = number + 1;
			if(new_number < option_name.length) {	
				options_save(option_name,option_value,new_number);
				} else {
				if(section_contents.length>0) {
					function_loader("output_content",[0]);
				}
			}
		},
		error: function(data, status, statusText, responsText) {
			log_to_console(statusText);
		}
	});
}

/**
	* This function is used to fetch the options and triggering a refresh of the display.
*/
function options_set() {
	
	var option_name_array = [];
	var option_value_array = [];
	
	items_per_page = $("input[name=items_per_page]").val();
	option_name_array.push("items_per_page");
	option_value_array.push($("input[name=items_per_page]").val());
	
	
	options_hide_integrated = Boolean($("input[name=Option_HideIntegrated]").prop("checked"));
	option_name_array.push("options_hide_integrated");
	option_value_array.push($("input[name=Option_HideIntegrated]").prop("checked"));
	
	
	options_hide_local = Boolean($("input[name=Option_HideLocal]").prop("checked"));
	option_name_array.push("options_hide_local");
	option_value_array.push($("input[name=Option_HideLocal]").prop("checked"));
	
	
	options_hide_empty_subtitles = Boolean($("input[name=Option_HideEmptySubtitles]").prop("checked"));
	option_name_array.push("options_hide_empty_subtitles");
	option_value_array.push($("input[name=Option_HideEmptySubtitles]").prop("checked"));
	
	
	options_only_multiple = Boolean($("input[name=Option_ShowOnlyMultiple]").prop("checked"));
	option_name_array.push("options_only_multiple");
	option_value_array.push($("input[name=Option_ShowOnlyMultiple]").prop("checked"));
	
	options_auto_select_duplicate = Boolean($("input[name=Option_Autoselect]").prop("checked"));
	option_name_array.push("options_auto_select_duplicate");
	option_value_array.push($("input[name=Option_Autoselect]").prop("checked"));
	
	function_loader("options_save",[option_name_array,option_value_array,0]);
	
	
	log_add("Options Saved!");	
	
	return false;
}



////////////////////////////////////////////////////////////////////////////
// Functions for refreshing
////////////////////////////////////////////////////////////////////////////

/*
	Not yet implemented.
	Need to sort out how to monitor when it's done..
function refresh_movie_in_plex(mediakey) {
	
	
	$("#myModal").modal('hide');
	$.ajax({
		type: "PUT",
		url: baseurl + "/library/metadata/"+ mediakey +"/refresh",
		dataType: "text",
		global: false,
		success: function(data) {
			
			setTimeout(function() {
				section = get_section_info(selected_section);
				log_add("Started forced refresh in Plex on movie/episode: " + mediakey);
				section.refreshing = true;
			refresh_section_in_plex_verify()},3000);						
		},
		error: function(data, status, statusText, responsText) {
			log_to_console(data + statusText);
		},
		complete: function() {
			log_to_console("Initiated forced-refresh on movie/episode with key: " + mediakey);
			return true;
		}
	});	
}
*/

function refresh_section_in_plex() {
	$("#myModal").modal('hide');
	$.ajax({
		type: "GET",
		url: baseurl + "/library/sections/"+ selected_section +"/refresh?force=1",
		dataType: "text",
		global: false,
		success: function(data) {
			
			setTimeout(function() {
				section = get_section_info(selected_section);
				log_add("Started forced refresh in Plex on section: " + section.title);
				section.refreshing = true;
			refresh_section_in_plex_verify()},3000);						
		},
		error: function(data, status, statusText, responsText) {
			log_to_console(data + statusText);
		},
		complete: function() {
			log_to_console("Initiated forced-refresh on section with key: " + selected_section);
			return true;
		}
	});	
}

function refresh_section_in_plex_verify() {
 	$.ajax({
		type: "GET",
		url: baseurl + utility + "?Func=GetXMLFileFromUrl&Secret="+Secret+"&Url="+baseurl+"/library/sections/",
		dataType: "xml",
		cache: false,
		global: false,
		success: function(data) {
			
			$(data).find("Directory ").each(function() {
				section = get_section_info($(this).attr("key"));
				if(section.refreshing === true) {
					if($(this).attr("refreshing") == "0") {
						log_add("Section refresh in Plex completed on: " + section.title + ". Extra information may still be downloading from the Internet. You can refresh the fetched data by going to this section again.");
						//log_to_console("Section refresh in Plex completed on: " + section.title);
						section.refreshing = false;
					}	
				}			
			});
			
			for (i = 0; i < sections.length; i++) {
				if (sections[i].refreshing === true) {
					setTimeout(function() {refresh_section_in_plex_verify()},2000);
					break;
				}
			}
		},
		error: function(data, status, statusText, responsText) {
			log_to_console(data + statusText);
		},
		complete: function() {
			//log_to_console("Verified forced-refresh on key: " + selected_section + " and title: " + section.title);
			function_loader("output_content",[($("#PageBar .active span").html()-1)]);
			return true;
		}
	});	
}

// This section updates the sectionsbox to highlight what has been selected and to show the proper searchbox.
function refresh_section_list(LibraryKey, TriggeringElement) {
	selected_section = LibraryKey; // is this usefull?
	$("#MainBox").html(loadingScreen);
	$("#PageBar").html("");
	$("#LibraryBox span").removeClass("Bold");
	$(TriggeringElement).addClass("Bold");
	
	SearchBox = "<div class='VideoHeadline'>Search " + $(TriggeringElement).html() + "</div>";
	SearchBox += "<div class='VideoSubtitle'><input type='text' value='"+searchstring+"' name='searchstring'></div>";
	SearchBox += "<div class='VideoSubtitle'><input type='submit' name='searchbutton' class='btn btn-default btn-xs' value='Search'></div>";
	
	$("#SearchBox").html(SearchBox);
	$("#SearchBox").addClass("VideoBox");
	$("input[name=searchbutton]").attr("disabled", "disabled");
}

function reset_variables() {
	show_page = 0; // Default so we start at first page.
	section_contents = []; // Empty the array with items.
	searchstring = "";
}

////////////////////////////////////////////////////////////////////////////
// Functions for searching
////////////////////////////////////////////////////////////////////////////

function search_set() {
	if($("input[name=searchstring]").val().length === 0) {
		searchstring = "";
		output_content(0);		
		} else if($("input[name=searchstring]").val().length > 2) {
		searchstring = $("input[name=searchstring]").val();
		output_content(0);
		log_add("Searching for '"+searchstring+"' in titles.");
		} else {
		log_add("Minimum of 3 characters for searching.");
	}
}


/**
	* Do a refresh of displayed content after all ajaxes have done their thing.
*/
$(document).ajaxStop(function() {
	log_to_console("All ajax request completed.");
	//output_content(0);
	end_timer();
	log_add("Finished loading the section.");
});

function scrollTo(title) {
    location.hash = "#" + title;
}

// Force all ajax-calls to be non-cached.
//$.ajaxSetup({ cache: false });
//////////////////////////////////////
// "Classes"
//////////////////////////////////////
function Video() {
	this.active_subtitle_id = false;
	this.filename = "";
	this.hash = "";
	this.hide = false;
	this.id = "";
	this.key = "";
	this.summary = "";
	this.thumb = "";
	this.showKey = false;
	this.showRatingKey = false;
	this.seasonKey = false;
	this.seasonRatingKey = false;
	this.subtitles = [];
	this.parentTitle = "";
	this.parentKey = "";
	this.grandparentTitle = "";
	this.grandparentKey = "";
	this.title = "";
	this.type = "";
}
