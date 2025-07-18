function toggleAcreField() {
                const othersArea = document.getElementById('others_area');
                const acreFieldContainer = document.getElementById('acreFieldContainer');
                const othersAreaValue = othersArea.value.toUpperCase(); // Convert to uppercase for case-insensitive comparison

                // Hide acre field if empty or NA/N/A, show for other values
                if (othersAreaValue === '' || othersAreaValue === 'NA' || othersAreaValue === 'N/A') {
                    acreFieldContainer.style.display = 'none';
                    // Clear the acre value when hiding
                    document.getElementById('others_area_acre').value = '';
                    // Trigger the change event to update totals if needed
                    if (typeof get_total_area_acre === 'function') {
                        get_total_area_acre();
                    }
                } else {
                    acreFieldContainer.style.display = 'block';
                }
            }
            function check_general_water(value) {
                if (value == 'Yes') {
                    $('.general_water_details').show();
                }
                else {
                    $('.general_water_details').hide();
                }
            }

            function check_approach_road(value) {
                if (value == 'Yes') {
                    $('#approach_road_details').show();
                    $('#approach_road_details_table').show();
                }
                else {
                    $('#approach_road_details').hide();
                    $('#approach_road_details_table').hide();
                }
            }

            function check_blasting_radio(value) {
                if (value == 'Yes') {
                    $('.blasting_details').show();
                }
                else {
                    $('.blasting_details').hide();
                }
            }

            function check_power_line(value) {
                if (value == 'Yes') {
                    $('.power_line_details').show();
                    $('.power_line_details_table').hide();
                }
                else {
                    $('.power_line_details').hide();
                    $('.power_line_details_table').show();

                }
            }

            function check_wastewater(value) {
                if (value == 'Yes') {
                    $('.power_line_details').show();
                }
                else {
                    $('.power_line_details').hide();
                }
            }

            function check_industry_emission(value) {
                if (value == 'Yes') {
                    $('.power_line_details').show();
                }
                else {
                    $('.power_line_details').hide();
                }
            }

            function save_terrain_baseline_details(service) {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Common validations for all services
                const commonValidations = [
                    { id: 'bl_protected_area_name', errorId: 'bl_protected_area_nameErrorMsg', errorMsg: 'Enter Protected Area Name' },
                    { id: 'bl_protected_area_distance', errorId: 'bl_protected_area_distanceErrorMsg', errorMsg: 'Enter Protected Area Distance' },
                    // ... (keep all other common validations)
                ];

                // Service-specific validations
                const serviceValidations = {
                    IEE: [
                        { id: 'proosed_location_justification_value', errorId: 'proosed_location_justification_valueErrorMsg', errorMsg: 'Select One' },
                        { id: 'terrain_elevation', errorId: 'terrain_elevationErrorMsg', errorMsg: 'Enter Elevation (meters)' },
                        { id: 'terrain_slope', errorId: 'terrain_slopeErrorMsg', errorMsg: 'Select Slope/Gradient' }
                    ],
                    GEN: [
                        { id: 'terrain_elevation', errorId: 'terrain_elevationErrorMsg', errorMsg: 'Enter Elevation (meters)' },
                        { id: 'terrain_slope', errorId: 'terrain_slopeErrorMsg', errorMsg: 'Select Slope/Gradient' }
                    ],
                    default: []
                };

                // Combine validations based on service type
                const validations = [...commonValidations, ...(serviceValidations[service] || serviceValidations.default)];

                // Validate all fields
                let isValid = true;
                for (const validation of validations) {
                    const $field = $(`#${validation.id}`);
                    const value = $field.val();
                    if (!value || value.trim() === '') {
                        showBaselineErrorAndFocus(validation.errorId, validation.errorMsg, validation.id);
                        isValid = false;
                        break;
                    }
                }

                if (!isValid) return false;

                // Submit the form if all validations pass
                $.ajax({
                    type: "POST",
                    url: "/save_terrain_baseline_details/",
                    data: $('#terrain_baseline_form').serialize(),
                    success: function (data) {
                        const successCondition = data.message === 'success' || (service === 'IEE' && data.message === 'success');

                        if (successCondition) {
                            const $successMsg = $('#terrain_baseline_application_successMsg');
							$successMsg.html('<i class="uil-folder-heart me-1 h4 align-middle"></i> Saved Successfully')
								.show()
								.focus()[0].scrollIntoView({ behavior: 'smooth', block: 'center' });

                            setTimeout(() => {
									$successMsg.fadeOut('slow', () => {
										$("#ProjectDetailsBtn").removeAttr("disabled");
										$("#collapseProjectDetails").addClass("show");
										$("#collapseTwo").removeClass("show");
									});
								}, 3000);
                        } else {
                            showBaselineError('#terrain_baseline_application_errorMsg',
                                `Application Error: ${data.error || 'Unknown error occurred'}`);
                        }
                    },
                    error: function (xhr, status, error) {
                        showBaselineError('#terrain_baseline_application_errorMsg', `Request Error: ${error}`);
                    }
                });
            }

            // Renamed helper function to show error message and focus on the field
            function showBaselineError(selector, message) {
				const $errorMsg = $(selector);
				$errorMsg.html(`<i class="uil-folder-heart me-1 h4 align-middle"></i> ${message}`)
					.show()
					.focus()[0].scrollIntoView({ behavior: 'smooth', block: 'center' });

				setTimeout(() => $errorMsg.fadeOut('slow'), 3000);
			}

            // Main validation function
            function save_general_project_details() {
				// Hide all previous messages
				$('.alert-danger, #project_details_successMsg, #project_details_errorMsg').hide();

				const fieldDefinitions = {
					requiredFields: [
						{ id: 'project_objective', message: 'Enter Project Objective' },
						{ id: 'project_beneficiaries', message: 'Enter Project Beneficiaries' },
						{ id: 'proposed_route_reason', message: 'Enter Project Route' },
						{ id: 'project_cost', message: 'Enter Project Cost' },
						{ id: 'project_duration', message: 'Enter Project Duration' },
						{ id: 'right_of_way', message: 'Enter Right of Way' },
						{ id: 'length_of_transmission', message: 'Enter Length of Transmission/Distribution Line' },
						{ id: 'transmission_voltage_level', message: 'Enter Voltage Level' },
						{ id: 'starting_point_transmission', message: 'Enter Starting Point/Tapping Point' },
						{ id: 'transmission_termination_point', message: 'Enter Termination Point' }
					],
			function save_general_project_details()
            {
                let project_objective = $('#project_objective').val();
                let no_of_workers = $('#no_of_workers').val();
                let project_output = $('#project_output').val();
                let project_cost = $('#project_cost').val();
                let project_duration = $('#project_duration').val();
                
        
                if(project_objective == "")
                {
                    $('#project_objectiveErrorMsg').html("Enter Project Objective");
                    $('#project_objectiveErrorMsg').show();
                    $('#project_objectiveErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_objective').focus();
                }
                else if(no_of_workers == "")
                {
                    $('#no_of_workersErrorMsg').html("Enter No of Workers");
                    $('#no_of_workersErrorMsg').show();
                    $('#no_of_workersErrorMsg').delay(2000).fadeOut('slow');
                    $('#no_of_workers').focus();
                }
                else if(project_output == "")
                {
                    $('#project_outputErrorMsg').html("Enter Project Output");
                    $('#project_outputErrorMsg').show();
                    $('#project_outputErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_output').focus();
                }
                else if(project_cost == "")
                {
                    $('#project_costErrorMsg').html("Enter Project Cost");
                    $('#project_costErrorMsg').show();
                    $('#project_costErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_cost').focus();
                }
                else if(project_duration == "")
                {
                    $('#project_durationErrorMsg').html("Enter Project Duration");
                    $('#project_durationErrorMsg').show();
                    $('#project_durationErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_duration').focus();
                }
                else
                {
                    $.ajax
                    ({
                        type : "POST",
                        url : "/save_project_details/",
                        data : $('#project_details_form').serialize(),
                        success : function(data)
                        {
                            if(data.message == 'success')
							{
									$successMsg.html('<i class="uil-folder-heart me-1 h4 align-middle"></i> Saved Successfully')
									.show()
									.attr('tabindex', '-1')
									.focus()[0].scrollIntoView({ behavior: 'smooth', block: 'center' });

								setTimeout(() => {
									$successMsg.fadeOut('slow', () => {
										$("#collapseSixBtn").removeAttr("disabled");
										$("#collapseSix").addClass("show");
										$("#collapseProjectDetails").removeClass("show");
									});
								}, 2000);
                            }
                            else
                            {
                                var errorMsg = data.error;
                                $('#project_details_errorMsg').html(`Application Error: ${data.error}`);
                                $('#project_details_errorMsg').show();
                                setTimeout(function()
                                {
                                    $('#project_details_errorMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                            }
                        }
                    });
                }
            }



            function save_general_water_requirement() {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Get the water required value
                const water_required_value = $("input[name=water_required]:checked").val();
                const isWaterRequired = water_required_value === 'Yes';

                // Define validation groups
                const basicValidations = [
                    {
                        condition: $("input[name=water_excavated_muck]:checked").length < 1,
                        errorId: 'water_excavated_muckErrorMsg',
                        focusId: 'water_excavated_muck',
                        message: 'Please Select One.'
                    },
                    {
                        condition: $("input[name=water_required]:checked").length < 1,
                        errorId: 'water_requiredErrorMsg',
                        focusId: 'water_required',
                        message: 'Please Select One.'
                    }
                ];

                const waterRequiredValidations = [
                    { field: 'water_raw_material_source', condition: $('#water_raw_material_source').val() === "" },
                    { field: 'water_raw_material_qty_day', condition: $('#water_raw_material_qty_day').val() === "" },
                    { field: 'water_raw_material_recycle_day', condition: $('#water_raw_material_recycle_day').val() === "" },
                    { field: 'water_cleaning_source', condition: $('#water_cleaning_source').val() === "" },
                    { field: 'water_cleaning_qty_day', condition: $('#water_cleaning_qty_day').val() === "" },
                    { field: 'water_cleaning_recycle_day', condition: $('#water_cleaning_recycle_day').val() === "" },
                    { field: 'water_process_source', condition: $('#water_process_source').val() === "" },
                    { field: 'water_process_qty_day', condition: $('#water_process_qty_day').val() === "" },
                    { field: 'water_process_recycle_day', condition: $('#water_process_recycle_day').val() === "" },
                    { field: 'water_domestic_source', condition: $('#water_domestic_source').val() === "" },
                    { field: 'water_domestic_qty_day', condition: $('#water_domestic_qty_day').val() === "" },
                    { field: 'water_dust_compression_source', condition: $('#water_dust_compression_source').val() === "" },
                    { field: 'water_dust_compression_qty_day', condition: $('#water_dust_compression_qty_day').val() === "" },
                    { field: 'water_dust_compression_recycle_day', condition: $('#water_dust_compression_recycle_day').val() === "" },
                    { field: 'water_others_name', condition: $('#water_others_name').val() === "" },
                    { field: 'water_others_source', condition: $('#water_others_source').val() === "" },
                    { field: 'water_others_qty_day', condition: $('#water_others_qty_day').val() === "" },
                    { field: 'water_downstream_users', condition: $('#water_downstream_users').val() === "" },
                    { field: 'water_flow_rate_lean', condition: $('#water_flow_rate_lean').val() === "" },
                    { field: 'water_source_distance', condition: $('#water_source_distance').val() === "" }
                ];

                // Check basic validations
                for (const validation of basicValidations) {
                    if (validation.condition) {
                        showErrorAndFocus(validation.errorId, validation.message, validation.focusId);
                        return false;
                    }
                }

                // Check water required validations if applicable
                if (isWaterRequired) {
                    for (const validation of waterRequiredValidations) {
                        if (validation.condition) {
                            showErrorAndFocus(
                                `${validation.field}ErrorMsg`,
                                'Please Select One.',
                                validation.field
                            );
                            return false;
                        }
                    }
                }

                // If all validations pass, submit the form
                submitWaterRequirementForm();
            }

            function submitWaterRequirementForm() {
                $.ajax({
                    type: "POST",
                    url: "/save_general_water_requirement/",
                    data: $('#water_requirement_form').serialize(),
                    success: function (data) {
                        if (data.message === 'success') {
                            showSuccessMessage(
                                'water_requirement_application_successMsg',
                                'Saved Successfully',
                                function () {
                                    $("#headingFiveBtn").removeAttr("disabled");
                                    $("#collapseFive").addClass("show");
                                    $("#collapseFour").removeClass("show");
                                }
                            );
                        } else {
                            showErrorMessage(
                                'water_requirement_application_errorMsg',
                                data.error || 'Application Error'
                            );
                        }
                    },
                    error: function (xhr, status, error) {
                        showErrorMessage(
                            'water_requirement_application_errorMsg',
                            `Request Error: ${error}`
                        );
                    }
                });
            }

            function save_power_line_details() {
                application_no = $('#application_no').val();
                line_chainage_from = $('#line_chainage_from').val();
                line_chainage_to = $('#line_chainage_to').val();
                land_type = $('#land_type').val();
                terrain = $('#terrain').val();
                tower_type = $('#tower_type').val();
                no_of_tower = $('#no_of_tower').val();
                row = $('#row').val();
                area_required = $('#area_required').val();
                let csrf_token = $('input[name="csrfmiddlewaretoken"]').val();

                if (line_chainage_from == "") {
                    $('#line_chainage_fromErrorMsg').html("Enter Transmission line Chainage From");
                    $('#line_chainage_fromErrorMsg').show();
                    $('#line_chainage_fromErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (line_chainage_to == "") {
                    $('#line_chainage_toErrorMsg').html("Enter Transmission line Chainage To");
                    $('#line_chainage_toErrorMsg').show();
                    $('#line_chainage_toErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (land_type == "") {
                    $('#land_typeErrorMsg').html("Enter Land Type");
                    $('#land_typeErrorMsg').show();
                    $('#land_typeErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (terrain == "") {
                    $('#terrainErrorMsg').html("Select One ");
                    $('#terrainErrorMsg').show();
                    $('#terrainErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (tower_type == "") {
                    $('#tower_typeErrorMsg').html("Enter Type of Tower");
                    $('#tower_typeErrorMsg').show();
                    $('#tower_typeErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (no_of_tower == "") {
                    $('#no_of_towerErrorMsg').html("Enter No. of Towers");
                    $('#no_of_towerErrorMsg').show();
                    $('#no_of_towerErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (row == "") {
                    $('#rowErrorMsg').html("Enter Right of way");
                    $('#rowErrorMsg').show();
                    $('#rowErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (area_required == "") {
                    $('#area_requiredErrorMsg').html("Enter Area Required");
                    $('#area_requiredErrorMsg').show();
                    $('#area_requiredErrorMsg').delay(2000).fadeOut('slow');
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_anc_power_line_details/",
                            data: { 'application_no': application_no, 'line_chainage_from': line_chainage_from, 'line_chainage_to': line_chainage_to, 'land_type': land_type, 'terrain': terrain, 'tower_type': tower_type, 'no_of_tower': no_of_tower, 'row': row, 'area_required': area_required, csrfmiddlewaretoken: csrf_token },
                            success: function (responseText) {
                                $('#power_line_successMsg').html("Power Line Details Added Successfully");
                                $('#power_line_successMsg').show();
                                $('#power_line_successMsg').delay(2000).fadeOut('slow');
                                setTimeout(function () {
                                    $('#anc_power_line_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#anc_power_line_details').html(responseText);
                                }, 2000);
                                setTimeout(function () {
                                    $('#anc_power_line_form')[0].reset();
                                }, 2000);
                            }
                        });
                }
            }

            function save_anc_approach_road_details(service) {
                let anc_road_required = $("input[name=anc_road_required]:checked").length;
                let anc_road_required_value = $("input[name=anc_road_required]:checked").val();
                let anc_road_length = $('#anc_road_length').val();
                let anc_road_start_point = $('#anc_road_start_point').val();
                let anc_road_end_point = $('#anc_road_end_point').val();
                let anc_road_blast_required = $("input[name=anc_road_required]:checked").length;
                let anc_road_blast_required_value = $("input[name=anc_road_required]:checked").val();
                let anc_road_blast_type = $('#anc_road_blast_type').val();
                let anc_road_blast_qty = $('#anc_road_blast_qty').val();
                let anc_road_blast_location = $('#anc_road_blast_location').val();
                let anc_road_blast_frequency_time = $('#anc_road_blast_frequency_time').val();

                if (anc_road_required < 1) {
                    $('#anc_road_requiredErrorMsg').html("Please Select One.");
                    $('#anc_road_requiredErrorMsg').show();
                    $('#anc_road_requiredErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_required').focus();
                }
                else if (anc_road_required_value == 'Yes' && anc_road_length == "") {
                    $('#anc_road_lengthErrorMsg').html("Enter Length of road in km.");
                    $('#anc_road_lengthErrorMsg').show();
                    $('#anc_road_lengthErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_length').focus();
                }
                else if (anc_road_required_value == 'Yes' && anc_road_start_point == "") {
                    $('#anc_road_start_pointErrorMsg').html("Enter Starting Point.");
                    $('#anc_road_start_pointErrorMsg').show();
                    $('#anc_road_start_pointErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_start_point').focus();
                }
                else if (anc_road_required_value == 'Yes' && anc_road_end_point == "") {
                    $('#anc_road_end_pointErrorMsg').html("Enter Termination Point.");
                    $('#anc_road_end_pointErrorMsg').show();
                    $('#anc_road_end_pointErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_end_point').focus();
                }
                else if (anc_road_blast_required < 1) {
                    $('#anc_road_blast_requiredErrorMsg').html("Enter Termination Point.");
                    $('#anc_road_blast_requiredErrorMsg').show();
                    $('#anc_road_blast_requiredErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_blast_required').focus();
                }
                else if (anc_road_blast_required_value == 'Yes' && anc_road_blast_type == "") {
                    $('#anc_road_blast_typeErrorMsg').html("Mention type of blasting.");
                    $('#anc_road_blast_typeErrorMsg').show();
                    $('#anc_road_blast_typeErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_blast_type').focus();
                }
                else if (anc_road_blast_required_value == 'Yes' && anc_road_blast_qty == "") {
                    $('#anc_road_blast_qtyErrorMsg').html("Enter Type and quantity of explosive to be used.");
                    $('#anc_road_blast_qtyErrorMsg').show();
                    $('#anc_road_blast_qtyErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_blast_qty').focus();
                }
                else if (anc_road_blast_required_value == 'Yes' && anc_road_blast_location == "") {
                    $('#anc_road_blast_locationErrorMsg').html("Mention location (s) where blasting is required.");
                    $('#anc_road_blast_locationErrorMsg').show();
                    $('#anc_road_blast_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_blast_location').focus();
                }
                else if (anc_road_blast_required_value == 'Yes' && anc_road_blast_frequency_time == "") {
                    $('#anc_road_blast_frequency_timeErrorMsg').html("Enter Frequency and timing of blasting per day.");
                    $('#anc_road_blast_frequency_timeErrorMsg').show();
                    $('#anc_road_blast_frequency_timeErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_road_blast_frequency_time').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_anc_approach_road_details/",
                            data: $('#ancillary_approach_road_form').serialize(),
                            success: function (data) {
                                if (service == 'IEE') {
                                    if (data.message == 'success') {
                                        $('#anc_approach_road_successMsg').html("Saved Successfully");
                                        $('#anc_approach_road_successMsg').show();
                                        $('#anc_approach_road_successMsg').focus();
                                        setTimeout(function () {
                                            $('#anc_approach_road_successMsg').delay(2000).fadeOut('slow');
                                        }, 2000);
                                        setTimeout(function () {
                                            $("#headingSixBtn").removeAttr("disabled");
                                            $("#collapseSix").addClass("show");
                                            $("#collapseFive").removeClass("show");
                                        }, 2000);
                                    }
                                    else {
                                        var errorMsg = data.error;

                                        $('#anc_approach_road_errorMsg').html(`Application Error: ${data.error}`);
                                        $('#anc_approach_road_errorMsg').show();
                                        $('#anc_approach_road_errorMsg').focus();
                                        setTimeout(function () {
                                            $('#anc_approach_road_errorMsg').delay(2000).fadeOut('slow');
                                        }, 2000);
                                    }
                                }
                                else {
                                    if (data.message == 'success') {
                                        $('#anc_approach_road_successMsg').html("Saved Successfully");
                                        $('#anc_approach_road_successMsg').show();
                                        setTimeout(function () {
                                            $('#anc_approach_road_successMsg').delay(2000).fadeOut('slow');
                                        }, 2000);
                                        setTimeout(function () {
                                            $("#headingSevenBtn").removeAttr("disabled");
                                            $("#collapseSeven").addClass("show");
                                            $("#collapseFive").removeClass("show");
                                        }, 2000);
                                    }
                                    else {
                                        $('#anc_approach_road_errorMsg').html("Please Check And Submit Again");
                                        $('#anc_approach_road_errorMsg').show();
                                        setTimeout(function () {
                                            $('#anc_approach_road_errorMsg').delay(2000).fadeOut('slow');
                                        }, 2000);
                                    }
                                }
                            }
                        });
                }
            }

            function save_anc_other_details() {
                $.ajax
                    ({
                        type: "POST",
                        url: "/save_anc_other_details/",
                        data: $('#anc_others_form').serialize(),
                        success: function (data) {
                            if (data.message == 'success') {
                                $('#anc_others_successMsg').html("Saved Successfully");
                                $('#anc_others_successMsg').show();
                                setTimeout(function () {
                                    $('#anc_others_successMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $("#headingEightBtn").removeAttr("disabled");
                                    $("#collapseEight").addClass("show");
                                    $("#collapseSeven").removeClass("show");
                                }, 2000);
                            }
                            else {
                                var errorMsg = data.error;
                                $('#anc_others_errorMsg').html(`Application Error: ${data.error}`);
                                $('#anc_others_errorMsg').show();
                                setTimeout(function () {
                                    $('#anc_others_errorMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                            }
                        }
                    });
            }

            function save_solid_waste_details(service) {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Define all waste types and their fields
                const wasteTypes = [
                    {
                        name: 'hazardous',
                        fields: ['list', 'source', 'qty_annum', 'mgt_plan'],
                        errorMessages: {
                            list: "List the hazardous waste types",
                            source: "Specify hazardous waste sources",
                            qty_annum: "Enter hazardous waste quantity per annum",
                            mgt_plan: "Provide hazardous waste management plan"
                        }
                    },
                    {
                        name: 'non_hazardous',
                        fields: ['list', 'source', 'qty_annum', 'mgt_plan'],
                        errorMessages: {
                            list: "List the non-hazardous waste types",
                            source: "Specify non-hazardous waste sources",
                            qty_annum: "Enter non-hazardous waste quantity per annum",
                            mgt_plan: "Provide non-hazardous waste management plan"
                        }
                    },
                    {
                        name: 'medical',
                        fields: ['list', 'source', 'qty_annum', 'mgt_plan'],
                        errorMessages: {
                            list: "List the medical waste types",
                            source: "Specify medical waste sources",
                            qty_annum: "Enter medical waste quantity per annum",
                            mgt_plan: "Provide medical waste management plan"
                        }
                    },
                    {
                        name: 'ewaste',
                        fields: ['list', 'source', 'qty_annum', 'mgt_plan'],
                        errorMessages: {
                            list: "List the e-waste types",
                            source: "Specify e-waste sources",
                            qty_annum: "Enter e-waste quantity per annum",
                            mgt_plan: "Provide e-waste management plan"
                        }
                    },
                    {
                        name: 'others',
                        fields: ['list', 'source', 'qty_annum', 'mgt_plan'],
                        errorMessages: {
                            list: "List other waste types",
                            source: "Specify other waste sources",
                            qty_annum: "Enter other waste quantity per annum",
                            mgt_plan: "Provide other waste management plan"
                        }
                    }
                ];

                // Check budget field first
                if ($('#en_impact_allocated_budget').val() === "") {
                    showErrorAndFocus(
                        'en_impact_allocated_budgetErrorMsg',
                        'Provide an allocated budget for the management plan proposed',
                        'en_impact_allocated_budget'
                    );
                    return false;
                }

                // Validate all waste type fields
                for (const wasteType of wasteTypes) {
                    for (const field of wasteType.fields) {
                        const fieldId = `en_impact_${wasteType.name}_waste_${field}`;
                        if ($(`#${fieldId}`).val() === "") {
                            showErrorAndFocus(
                                `${fieldId}ErrorMsg`,
                                wasteType.errorMessages[field],
                                fieldId
                            );
                            return false;
                        }
                    }
                }

                // If all validations pass, submit the form
                submitSolidWasteForm();
            }

            function submitSolidWasteForm() {
                $.ajax({
                    type: "POST",
                    url: "/save_solid_waste_details/",
                    data: $('#solid_waste_form').serialize(),
                    success: function (data) {
                        if (service == 'IEE') {
                            if (data.message == 'success') {
                                $('#solid_waste_successMsg').html("Saved Successfully");
                                $('#solid_waste_successMsg').show();
                                $('#solid_waste_successMsg').focus();
                                setTimeout(function () {
                                    $('#solid_waste_successMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $("#headingNineBtn").removeAttr("disabled");
                                    $("#collapseNine").addClass("show");
                                    $("#collapseEight").removeClass("show");
                                }, 2000);
                            }
                            else {
                                var errorMsg = data.error;

                                $('#solid_waste_errorMsg').html(`Application Error: ${data.error}`);
                                $('#solid_waste_errorMsg').show();
                                $('#solid_waste_errorMsg').focus();
                                setTimeout(function () {
                                    $('#solid_waste_errorMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                            }
                        }
                        else {
                            if (data.message === 'success') {
                                showSuccessMessage(
                                    'solid_waste_successMsg',
                                    'Saved Successfully',
                                    function () {
                                        $("#headingTwelveBtn").removeAttr("disabled");
                                        $("#collapseTwelve").addClass("show");
                                        $("#collapseEight").removeClass("show");
                                    }
                                );
                            } else {
                                showErrorMessage(
                                    'solid_waste_errorMsg',
                                    data.error || 'Application Error'
                                );
                            }
                        }
                    },
                    error: function (xhr, status, error) {
                        showErrorMessage(
                            'solid_waste_errorMsg',
                            `Request Error: ${error}`
                        );
                    }
                });
            }

            function save_noise_level_details() {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Define all noise area types and their fields
                const noiseAreas = [
                    {
                        type: 'ind_area',
                        fields: [
                            { name: 'day', message: 'Enter industrial area daytime noise level' },
                            { name: 'night', message: 'Enter industrial area nighttime noise level' },
                            { name: 'mgt_plan', message: 'Provide industrial area noise management plan' }
                        ]
                    },
                    {
                        type: 'mixed_area',
                        fields: [
                            { name: 'day', message: 'Enter mixed area daytime noise level' },
                            { name: 'night', message: 'Enter mixed area nighttime noise level' },
                            { name: 'mgt_plan', message: 'Provide mixed area noise management plan' }
                        ]
                    },
                    {
                        type: 'sen_area',
                        fields: [
                            { name: 'day', message: 'Enter sensitive area daytime noise level' },
                            { name: 'night', message: 'Enter sensitive area nighttime noise level' },
                            { name: 'mgt_plan', message: 'Provide sensitive area noise management plan' }
                        ]
                    }
                ];

                // Validate all noise area fields
                for (const area of noiseAreas) {
                    for (const field of area.fields) {
                        const fieldId = `en_noise_${area.type}_${field.name}`;
                        if ($(`#${fieldId}`).val() === "") {
                            showErrorAndFocus(
                                `${fieldId}ErrorMsg`,
                                field.message,
                                fieldId
                            );
                            return false;
                        }
                    }
                }

                // If all validations pass, submit the form
                submitNoiseLevelForm();
            }

            function submitNoiseLevelForm() {
                $.ajax({
                    type: "POST",
                    url: "/save_noise_level_details/",
                    data: $('#noise_level_form').serialize(),
                    success: function (data) {
                        if (data.message === 'success') {
                            showSuccessMessage(
                                'noise_level_successMsg',
                                'Saved Successfully',
                                function () {
                                    $("#otherImpactsBtn").removeAttr("disabled");
                                    $("#collapseOtherImpacts").addClass("show");
                                    $("#collapseTwelve").removeClass("show");
                                }
                            );
                        } else {
                            showErrorMessage(
                                'noise_level_errorMsg',
                                data.error || 'Application Error'
                            );
                        }
                    },
                    error: function (xhr, status, error) {
                        showErrorMessage(
                            'noise_level_errorMsg',
                            `Request Error: ${error}`
                        );
                    }
                });
            }

            function save_other_impact_details() {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Define all impact types and their fields
                const impactTypes = [
                    { name: 'odour', label: 'Odour' },
                    { name: 'fugutive', label: 'Fugitive' },
                    { name: 'slope', label: 'Slope' },
                    { name: 'aesthetic', label: 'Aesthetic' },
                    { name: 'mucks', label: 'Mucks' },
                    { name: 'sewerage', label: 'Sewerage' },
                    { name: 'erosion', label: 'Erosion' },
                    { name: 'storm_water', label: 'Storm Water' },
                    { name: 'habitat', label: 'Habitat' },
                    { name: 'socio', label: 'Socio' },
                    { name: 'water_source', label: 'Water Source' },
                    { name: 'other', label: 'Other' }
                ];

                // Field types for each impact
                const fieldTypes = [
                    { suffix: 'source', message: 'Enter source of {label} impact' },
                    { suffix: 'qty', message: 'Enter quantity of {label} impact' },
                    { suffix: 'mgt_plan', message: 'Provide management plan for {label} impact' }
                ];

                // Validate all impact fields
                for (const impact of impactTypes) {
                    for (const field of fieldTypes) {
                        const fieldId = `en_other_impact_${impact.name}_${field.suffix}`;
                        if ($(`#${fieldId}`).val() === "") {
                            const message = field.message.replace('{label}', impact.label);
                            showErrorAndFocus(
                                `${fieldId}ErrorMsg`,
                                message,
                                fieldId
                            );
                            return false;
                        }
                    }
                }

                // If all validations pass, submit the form
                submitOtherImpactForm();
            }

            function submitOtherImpactForm() {
                $.ajax({
                    type: "POST",
                    url: "/save_other_impact_details/",
                    data: $('#other_impact_form').serialize(),
                    success: function (data) {
                        if (data.message === 'success') {
                            showSuccessMessage(
                                'other_impact_successMsg',
                                'Saved Successfully',
                                function () {
                                    $("#headingAttachmentBtn").removeAttr("disabled");
                                    $("#collapseAttachment").addClass("show");
                                    $("#collapseOtherImpacts").removeClass("show");
                                }
                            );
                        } else {
                            showErrorMessage(
                                'other_impact_errorMsg',
                                data.error || 'Application Error'
                            );
                        }
                    },
                    error: function (xhr, status, error) {
                        showErrorMessage(
                            'other_impact_errorMsg',
                            `Request Error: ${error}`
                        );
                    }
                });
            }

            function save_general_attachment_details() {
                $('#general_attachment_successMsg').html("Saved Successfully");
                $('#general_attachment_successMsg').show();
                setTimeout(function () {
                    $('#general_attachment_successMsg').delay(2000).fadeOut('slow');
                }, 2000);
                setTimeout(function () {
                    $("#headingDisclaimerBtn").removeAttr("disabled");
                    $("#collapseDisclaimer").addClass("show");
                    $("#collapseAttachment").removeClass("show");
                }, 2000);
            }

            function submit_general_application() {
                $("#pageloader").show();
                $.ajax
                    ({
                        type: "POST",
                        url: "/submit_general_application/",
                        data: $('#general_submit_form').serialize(),
                        success: function (data) {
                            $("#pageloader").hide();
                            if (data.message == 'success') {
                                $('#general_submit_successMsg').html("Application Submitted Successfully");
                                $('#general_submit_successMsg').show();
                                setTimeout(function () {
                                    $('#general_submit_successMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    location.reload()
                                }, 2000);
                            }
                            else if (data.message == 'not submitted') {
                                $('#iee_submit_errorMsg').html("Please Submit Your Ancillary First And Try Again");
                                $('#iee_submit_errorMsg').show();
                                setTimeout(function () {
                                    $('#iee_submit_errorMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                            }
                            else {
                                var errorMsg = data.error;

                                $('#application_form_errorMsg').html(`Application Error: ${data.error}`);
                                $('#application_form_errorMsg').show();
                                $('#application_form_errorMsg').focus();

                                setTimeout(function () {
                                    $('#application_form_errorMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                            }
                        }
                    });
            }


            function add_machine_tool_details() {
                let application_no = $('#application_no').val();
                let machine_tool = $('#machine_tool').val();
                let machine_tool_qty = $('#machine_tool_qty').val();
                let machine_tool_installed_capacity = $('#machine_tool_installed_capacity').val();

                if (machine_tool == "") {
                    $('#machine_toolErrorMsg').html("Enter Machine/Tool/Equipment");
                    $('#machine_toolErrorMsg').show();
                    $('#machine_toolErrorMsg').delay(2000).fadeOut('slow');
                    $('#machine_tool').focus();
                }
                else if (machine_tool_qty == "") {
                    $('#machine_tool_qtyErrorMsg').html("Enter Qty");
                    $('#machine_tool_qtyErrorMsg').show();
                    $('#machine_tool_qtyErrorMsg').delay(2000).fadeOut('slow');
                    $('#machine_tool_qty').focus();
                }
                else if (machine_tool_installed_capacity == "") {
                    $('#machine_tool_installed_capacityErrorMsg').html("Enter Installed Capacity");
                    $('#machine_tool_installed_capacityErrorMsg').show();
                    $('#machine_tool_installed_capacityErrorMsg').delay(2000).fadeOut('slow');
                    $('#machine_tool_installed_capacity').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/add_machine_tool_details/",
                            data: { 'application_no': application_no, 'machine_tool': machine_tool, 'machine_tool_qty': machine_tool_qty, 'machine_tool_installed_capacity': machine_tool_installed_capacity },
                            success: function (responseText) {
                                $('#machine_tool_SuccessMsg').html("Add Successful");
                                $('#machine_tool_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#machine_tool_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#machine_equipment_tool_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#machine_details_div').html(responseText);
                                }, 2000);
                                $('#machine_equipment_tool_form')[0].reset();
                            }
                        });
                }
            }

            function machine_equipment_populate(record_id, application_no, machine_name, qty, installed_capacity) {
                $('#edit_machine_tool_record_id').val(record_id)
                $('#edit_machine_tool_app_no').val(application_no)
                $('#edit_machine_tool').val(machine_name);
                $('#edit_machine_tool_qty').val(qty);
                $('#edit_machine_tool_installed_capacity').val(installed_capacity);
                $('#edit_machine_equipment_tool_modal').modal('show');
            }

            function update_machine_equipment_populate() {
                let record_id = $('#edit_machine_tool_record_id').val();
                let application_no = $('#edit_machine_tool_app_no').val();
                let machine_tool = $('#edit_machine_tool').val();
                let qty = $('#edit_machine_tool_qty').val();
                let machine_tool_installed_capacity = $('#edit_machine_tool_installed_capacity').val();

                if (machine_tool == "") {
                    $('#edit_machine_toolErrorMsg').html("Enter Machine/Tool/Equipment");
                    $('#edit_machine_toolErrorMsg').show();
                    $('#edit_machine_toolErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_machine_tool').focus();
                }
                else if (machine_tool_qty == "") {
                    $('#edit_machine_tool_qtyErrorMsg').html("Enter Qty");
                    $('#edit_machine_tool_qtyErrorMsg').show();
                    $('#edit_machine_tool_qtyErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_machine_tool_qty').focus();
                }
                else if (machine_tool_installed_capacity == "") {
                    $('#edit_machine_tool_installed_capacityErrorMsg').html("Enter Installed Capacity");
                    $('#edit_machine_tool_installed_capacityErrorMsg').show();
                    $('#edit_machine_tool_installed_capacityErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_machine_tool_installed_capacity').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/update_machine_tool_details/",
                            data: { 'record_id': record_id, 'application_no': application_no, 'machine_tool': machine_tool, 'machine_tool_qty': machine_tool_qty, 'machine_tool_installed_capacity': machine_tool_installed_capacity },
                            success: function (responseText) {
                                $('#edit_machine_tool_SuccessMsg').html("Add Successful");
                                $('#edit_machine_tool_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#edit_machine_tool_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#edit_machine_equipment_tool_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#machine_details_div').html(responseText);
                                }, 2000);
                            }
                        });
                }
            }

            function populate_delete_machine_equipment(record_id, application_no) {
                $('#delete_machine_tool_record_id').val(record_id);
                $('#delete_machine_tool_app_no').val(application_no);
                $('#delete_machine_equipment_tool_modal').modal('show');
            }

            function delete_machine_tool_details() {
                let record_id = $('#delete_machine_tool_record_id').val();
                let application_no = $('#delete_machine_tool_app_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_machine_tool_details/",
                        data: { 'record_id': record_id, 'application_no': application_no },
                        success: function (responseText) {
                            $('#delete_machine_tool_SuccessMsg').html("Add Successful");
                            $('#delete_machine_tool_SuccessMsg').show();
                            setTimeout(function () {
                                $('#delete_machine_tool_SuccessMsg').delay(2000).fadeOut('slow');
                            }, 2000);
                            setTimeout(function () {
                                $('#delete_machine_equipment_tool_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#machine_details_div').html(responseText);
                            }, 2000);
                        }
                    });
            }

            function add_raw_material_details() {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Get form values
                const formData = {
                    application_no: $('#application_no').val(),
                    raw_material: $('#raw_material').val(),
                    qty: $('#raw_material_qty').val(),
                    source: $('#raw_material_source').val(),
                    storage_method: $('#raw_material_storage_method').val(),
                    csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val() // Fixed CSRF token retrieval
                };

                // Validation rules
                const validations = [
                    { field: 'raw_material', errorId: 'raw_materialErrorMsg', message: 'Enter Raw Material' },
                    { field: 'raw_material_qty', errorId: 'raw_material_qtyErrorMsg', message: 'Enter Qty' },
                    { field: 'raw_material_source', errorId: 'raw_material_sourceErrorMsg', message: 'Enter Source' },
                    { field: 'raw_material_storage_method', errorId: 'raw_material_storage_methodErrorMsg', message: 'Select Storage Method' }
                ];

                // Validate fields
                for (const validation of validations) {
                    if (!formData[validation.field]) {
                        $(`#${validation.errorId}`).html(validation.message).show().delay(2000).fadeOut('slow');
                        $(`#${validation.field}`).focus();
                        return false;
                    }
                }

                // AJAX request
                $.ajax({
                    type: "POST",
                    url: "/add_raw_materials/",
                    data: formData,
                    success: function (responseText) {
                        $('#raw_material_SuccessMsg').html("Add Successful").show();

                        // Chain timeouts for better readability
                        setTimeout(function () {
                            $('#raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                            $('#raw_materials_modal').modal('hide');
                            $('#raw_materials_div').html(responseText);
                            $('#raw_materials_form')[0].reset();
                        }, 2000);
                    },
                    error: function (xhr, status, error) {
                        $('#raw_material_SuccessMsg').html("Error: " + error).show().delay(2000).fadeOut('slow');
                    }
                });
            }

            function raw_materials_details_edit(record_id, application_no, raw_material, qty, source, storage_method) {
                $('#edit_raw_material_record_id').val(record_id);
                $('#edit_raw_material_app_no').val(application_no);
                $('#edit_raw_material').val(raw_material);
                $('#edit_raw_material_qty').val(qty);
                $('#edit_raw_material_source').val(source);
                $('#edit_raw_material_storage_method').val(storage_method);
                $('#edit_raw_materials_modal').modal('show');
            }

            function update_raw_material_details() {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Get form values - verified field names match
                const formData = {
                    record_id: $('#edit_raw_material_record_id').val(),
                    application_no: $('#edit_raw_material_app_no').val(),
                    raw_material: $('#edit_raw_material').val(),
                    qty: $('#edit_raw_material_qty').val(),  // Note: Changed to match server expectation
                    source: $('#edit_raw_material_source').val(),  // Changed to match server expectation
                    storage_method: $('#edit_raw_material_storage_method').val(),  // Changed to match server expectation
                    csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()  // Fixed CSRF token
                };

                // Validation rules with correct field IDs
                const validations = [
                    {
                        field: 'edit_raw_material',
                        errorId: 'raw_materialErrorMsg',
                        message: 'Enter Raw Material'
                    },
                    {
                        field: 'edit_raw_material_qty',
                        errorId: 'raw_material_qtyErrorMsg',
                        message: 'Enter Qty'
                    },
                    {
                        field: 'edit_raw_material_source',
                        errorId: 'raw_material_sourceErrorMsg',
                        message: 'Enter Source'
                    },
                    {
                        field: 'edit_raw_material_storage_method',
                        errorId: 'raw_material_storage_methodErrorMsg',
                        message: 'Select Storage Method'
                    }
                ];

                // Validate fields
                for (const validation of validations) {
                    const value = $(`#${validation.field}`).val();
                    if (!value) {
                        $(`#${validation.errorId}`).html(validation.message).show().delay(2000).fadeOut('slow');
                        $(`#${validation.field}`).focus();
                        return false;
                    }
                }

                // AJAX request
                $.ajax({
                    type: "POST",
                    url: "/update_raw_materials/",
                    data: formData,
                    success: function (responseText) {
                        $('#edit_raw_material_SuccessMsg').html("Update Successful").show();

                        // Combined timeouts for better performance
                        setTimeout(function () {
                            $('#edit_raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                            $('#edit_raw_materials_modal').modal('hide');
                            $('#raw_materials_div').html(responseText);
                        }, 2000);
                    },
                    error: function (xhr, status, error) {
                        $('#edit_raw_material_SuccessMsg').html("Error: " + error).show().delay(2000).fadeOut('slow');
                    }
                });
            }

            function populate_delete_raw_materials(record_id, application_no) {
                $('#delete_raw_material_record_id').val(record_id);
                $('#delete_raw_material_app_no').val(application_no);
                $('#delete_raw_material_modal').modal('show');
            }

            function delete_raw_material_details() {
                let record_id = $('#delete_raw_material_record_id').val();
                let application_no = $('#delete_raw_material_app_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_raw_materials/",
                        data: { 'record_id': record_id, 'application_no': application_no, csrfmiddlewaretoken: '{{ csrf_token }}' },
                        success: function (responseText) {
                            $('#delete_raw_material_SuccessMsg').html("Delete Successful");
                            $('#delete_raw_material_SuccessMsg').show();
                            setTimeout(function () {
                                $('#delete_raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                            }, 2000);
                            setTimeout(function () {
                                $('#delete_raw_material_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#raw_materials_div').html(responseText);
                            }, 2000);
                        }
                    });
            }

            function add_partner_details() {
                let application_no = $('#application_no').val();
                let partner_type = $('#partner_type').val();
                let partner_type_name = $('#partner_type_name').val();
                let partner_type_address = $('#partner_type_address').val();

                if (partner_type == "") {
                    $('#partner_typeErrorMsg').html("Enter Partner Type");
                    $('#partner_typeErrorMsg').show();
                    $('#partner_typeErrorMsg').delay(2000).fadeOut('slow');
                    $('#partner_type').focus();
                }
                else if (partner_type_name == "") {
                    $('#partner_type_nameErrorMsg').html("Enter Name");
                    $('#partner_type_nameErrorMsg').show();
                    $('#partner_type_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#partner_type_name').focus();
                }
                else if (partner_type_address == "") {
                    $('#partner_type_addressErrorMsg').html("Enter Address");
                    $('#partner_type_addressErrorMsg').show();
                    $('#partner_type_addressErrorMsg').delay(2000).fadeOut('slow');
                    $('#partner_type_address').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/add_product_details/",
                            data: { 'application_no': application_no, 'partner_type': partner_type, 'partner_type_name': partner_type_name, 'partner_type_address': partner_type_address },
                            success: function (responseText) {
                                $('#partner_type_SuccessMsg').html("Add Successful");
                                $('#partner_type_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#partner_type_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#partner_details_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#partner_details_div').html(responseText);
                                }, 2000);
                                $('#partner_details_form')[0].reset();
                            }
                        });
                }
            }

            function populate_delete_partner_details(record_id, application_no) {
                $('#delete_partner_record_id').val(record_id);
                $('#delete_partner_app_no').val(application_no);
                $('#delete_partner_details_modal').modal('show');
            }

            function delete_partner_details() {
                let record_id = $('#delete_partner_details_record_id').val();
                let application_no = $('#delete_partner_details_app_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_partner_details/",
                        data: { 'record_id': record_id, 'application_no': application_no },
                        success: function (responseText) {
                            $('#delete_raw_material_SuccessMsg').html("Add Successful");
                            $('#delete_raw_material_SuccessMsg').show();
                            setTimeout(function () {
                                $('#delete_raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                            }, 2000);
                            setTimeout(function () {
                                $('#delete_raw_material_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#raw_materials_div').html(responseText);
                            }, 2000);
                        }
                    });
            }

            function save_general_attachment() {
                let file_length = document.getElementById("general_attach");
                if (file_length.value.length < 1) {
                    $('#general_attachErrorMsg').html("Please Choose A Attachment");
                    $('#general_attachErrorMsg').show();
                    $('#general_attachErrorMsg').delay(2000).fadeOut('slow');
                }
                else {
                    var fileName = document.getElementById('general_attach').files[0].name;
                    var fd = new FormData();
                    var file = document.getElementById('general_attach').files[0];
                    fd.append('general_attach', file);
                    token_value = $("input[name=csrfmiddlewaretoken]").val();
                    $.ajaxSetup
                        ({
                            beforeSend: function (xhr, settings) {
                                xhr.setRequestHeader("X-CSRFToken", token_value);
                            }
                        });
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_general_attachment/",
                            data: fd,
                            dataType: 'json',
                            contentType: false,
                            processData: false,
                            success: function (data) {
                                if (data.form_is_valid) {
                                    let file_url = data.file_url;
                                    let application_no = $('#application_no').val();
                                    $.ajax
                                        ({
                                            type: "POST",
                                            url: "/save_general_attachment_details/",
                                            data: { 'application_no': application_no, 'filename': fileName, 'file_url': file_url },
                                            success: function (responseText) {
                                                $('#general_attachment_modal').modal('hide');
                                                $('#general_attachment').html(responseText);
                                                $('.modal-backdrop').remove();
                                                $('#general_attachment_form')[0].reset();
                                            }
                                        });
                                }
                                else {
                                    $('#general_attachErrorMsg').html("File Already Exists With Same Name. Please Upload Another File");
                                    $('#general_attachErrorMsg').show();
                                    $('#general_attachErrorMsg').delay(2000).fadeOut('slow');
                                }
                            }
                        });
                }
            }

            function save_power_line_details() {
                // Hide all previous messages
                $('.error-msg').hide();
                $('#power_line_successMsg').hide();

                // Get the form element
                const form = document.getElementById('anc_power_line_form');

                // Create FormData object from the form
                const formData = new FormData(form);

                // Add additional fields that might not be in the form
                formData.append('application_no', $('#application_no').val());

                // Define validation rules in order
                const validationRules = [
                    { field: 'line_chainage_from', message: 'Enter Transmission line Chainage From' },
                    { field: 'line_chainage_to', message: 'Enter Transmission line Chainage To' },
                    { field: 'land_type', message: 'Enter Land Type' },
                    { field: 'terrain', message: 'Select One' },
                    { field: 'tower_type', message: 'Enter Type of Tower' },
                    { field: 'no_of_tower', message: 'Enter No. of Towers' },
                    { field: 'row', message: 'Enter Right of way' },
                    { field: 'area_required', message: 'Enter Area Required' }
                ];

                // Validate fields in sequence
                for (const rule of validationRules) {
                    const value = formData.get(rule.field);
                    if (!value) {
                        showFieldError(rule.field, rule.message);
                        return false;
                    }
                }

                // If validation passes, submit the form
                submitPowerLineDetails(formData);
            }

            // AJAX submission function
            function submitPowerLineDetails(formData) {
                $.ajax({
                    type: "POST",
                    url: "/save_anc_power_line_details/",
                    data: formData,
                    processData: false,  // Required for FormData
                    contentType: false,  // Required for FormData
                    success: function (responseText) {
                        $('#power_line_successMsg').html("Added Successfully").show();
                        // Optionally clear the form or close the modal after success
                        setTimeout(() => {
                            $('#anc_power_line_modal').modal('hide');
                            // You might want to reload data or reset the form here
                        }, 2000);
                        setTimeout(() => {
                            $('#anc_power_line_details').responseText();
                            // You might want to reload data or reset the form here
                        }, 3000);

                    },
                    error: function (xhr, status, error) {
                        $('#power_line_errorMsg').html("Error: " + error).show();
                    }
                });
            }

            // Helper function to show field errors (unchanged)
            function showFieldError(fieldName, message) {
                const $errorElement = $(`#${fieldName}ErrorMsg`);
                const $inputElement = $(`#${fieldName}`);

                $errorElement.html(message).show();
                $inputElement.focus();

                // Scroll to the error field
                $('html, body').animate({
                    scrollTop: $inputElement.offset().top - 100
                }, 200);

                // Auto-hide error after delay
                $errorElement.delay(2000).fadeOut('slow');
            }


            function populate_power_line_details(record_id, application_no, line_chainage_from, line_chainage_to, land_type, terrain, tower_type, no_of_tower, row, area_required) {
                $('#edit_anc_record_id').val(record_id);
                $('#edit_anc_application_no').val(application_no);
                $('#edit_line_chainage_from').val(line_chainage_from);
                $('#edit_line_chainage_to').val(line_chainage_to);
                $('#edit_land_type').val(land_type);
                $('#edit_terrain').val(terrain);
                $('#edit_tower_type').val(tower_type);
                $('#edit_no_of_tower').val(no_of_tower);
                $('#edit_row').val(row);
                $('#edit_area_required').val(area_required);
                $('#edit_anc_power_line_modal').modal('show');
            }

            function populate_delete_power_line(record_id, application_no) {
                $('#delete_anc_record_id').val(record_id);
                $('#delete_anc_application_no').val(application_no);
                $('#delete_anc_power_line_modal').modal('show');
            }

            function delete_power_line_details() {
                let record_id = $('#delete_anc_record_id').val();
                let application_no = $('#delete_anc_application_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_anc_power_line_details/",
                        data: { 'record_id': record_id, 'application_no': application_no, csrfmiddlewaretoken: '{{ csrf_token }}' },
                        success: function (responseText) {
                            $('#delete_power_line_successMsg').html("Power Line Details Deleted Successfully");
                            $('#delete_power_line_successMsg').show();
                            $('#delete_power_line_successMsg').delay(2000).fadeOut('slow');
                            setTimeout(function () {
                                $('#delete_anc_power_line_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#anc_power_line_details').html(responseText);
                            }, 2000);
                        }
                    });
            }

            function update_power_line_details() {
                // Get all form values
                const record_id = $('#edit_anc_record_id').val();
                const application_no = $('#edit_anc_application_no').val();
                const line_chainage_from = $('#edit_line_chainage_from').val();
                const line_chainage_to = $('#edit_line_chainage_to').val();
                const land_type = $('#edit_land_type').val();
                const terrain = $('#edit_terrain').val();
                const tower_type = $('#edit_tower_type').val();
                const no_of_tower = $('#edit_no_of_tower').val();
                const row = $('#edit_row').val();
                const area_required = $('#edit_area_required').val();

                // Validation rules (field name : error message)
                const validationRules = {
                    'line_chainage_from': 'Enter Transmission line Chainage From',
                    'line_chainage_to': 'Enter Transmission line Chainage To',
                    'land_type': 'Enter Land Type',
                    'terrain': 'Select One',
                    'tower_type': 'Enter Type of Tower',
                    'no_of_tower': 'Enter No. of Towers',
                    'row': 'Enter Right of way',
                    'area_required': 'Enter Area Required'
                };

                // Validate each field
                for (const field in validationRules) {
                    if (!$(`#edit_${field}`).val()) {
                        $(`#${field}ErrorMsg`).html(validationRules[field]).show().delay(2000).fadeOut('slow');
                        return; // Stop if any validation fails
                    }
                }

                // If all validations pass, make the AJAX call
                $.ajax({
                    type: "POST",
                    url: "/update_anc_power_line_details/",
                    data: {
                        record_id: record_id,
                        application_no: application_no,
                        line_chainage_from: line_chainage_from,
                        line_chainage_to: line_chainage_to,
                        land_type: land_type,
                        terrain: terrain,
                        tower_type: tower_type,
                        no_of_tower: no_of_tower,
                        row: row,
                        area_required: area_required,
                        csrfmiddlewaretoken: '{{ csrf_token }}'
                    },
                    success: function (responseText) {
                        $('#edit_power_line_successMsg')
                            .html("Power Line Details Updated Successfully")
                            .show()
                            .delay(2000)
                            .fadeOut('slow');

                        setTimeout(function () {
                            $('#edit_anc_power_line_modal').modal('hide');
                        }, 2000);

                        setTimeout(function () {
                            $('#anc_power_line_details').html(responseText); // Same as original
                        }, 2000);
                    }
                });
            }

            function calculate_area_required() {
                let line_chainage_from_val = 0;
                let line_chainage_to_val = 0;
                let line_chainage_from = $('#line_chainage_from').val();
                let line_chainage_to = $('#line_chainage_to').val();
                let row = $('#row').val();

                if (line_chainage_from == "") {
                    line_chainage_from = line_chainage_from_val;
                }
                else {
                    line_chainage_to = line_chainage_to_val;
                }
                let sum_line_chainage = line_chainage_from + line_chainage_to;
                let total = row * sum_line_chainage;
                $('#area_required').val(total);
            }

            function calculate_edit_area_required() {
                let line_chainage_from_val = 0;
                let line_chainage_to_val = 0;
                let line_chainage_from = $('#edit_line_chainage_from').val();
                let line_chainage_to = $('#edit_line_chainage_to').val();
                let row = $('#edit_row').val();

                if (line_chainage_from == "") {
                    line_chainage_from = line_chainage_from_val;
                }
                else {
                    line_chainage_to = line_chainage_to_val;
                }
                let sum_line_chainage = line_chainage_from + line_chainage_to;
                let total = row * sum_line_chainage;
                $('#edit_area_required').val(total);
            }

            function save_anc_road_details() {
                let csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
                let application_no = $('#application_no').val();
                let road_line_chainage_from = $('#road_line_chainage_from').val();
                let road_line_chainage_to = $('#road_line_chainage_to').val();
                let road_land_type = $('#road_land_type').val();
                let road_terrain = $('#road_terrain').val();
                let road_width = $('#road_width').val();
                let road_row = $('#road_row').val();
                let road_area_required = $('#road_area_required').val();

                if (road_line_chainage_from == "") {
                    $('#road_line_chainage_fromErrorMsg').html("Enter Road Chainage From");
                    $('#road_line_chainage_fromErrorMsg').show();
                    $('#road_line_chainage_fromErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (road_line_chainage_to == "") {
                    $('#road_line_chainage_toErrorMsg').html("Enter Road Chainage To");
                    $('#road_line_chainage_toErrorMsg').show();
                    $('#road_line_chainage_toErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (road_land_type == "") {
                    $('#road_land_typeErrorMsg').html("Enter Land Type");
                    $('#road_land_typeErrorMsg').show();
                    $('#road_land_typeErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (road_terrain == "") {
                    $('#road_terrainErrorMsg').html("Select One ");
                    $('#road_terrainErrorMsg').show();
                    $('#road_terrainErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (road_width == "") {
                    $('#road_widthErrorMsg').html("Enter Road Width");
                    $('#road_widthErrorMsg').show();
                    $('#road_widthErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (road_row == "") {
                    $('#road_rowErrorMsg').html("Enter Right of way");
                    $('#road_rowErrorMsg').show();
                    $('#road_rowErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (road_area_required == "") {
                    $('#road_area_requiredErrorMsg').html("Enter Area Required");
                    $('#road_area_requiredErrorMsg').show();
                    $('#road_area_requiredErrorMsg').delay(2000).fadeOut('slow');
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_anc_road_details/",
                            data: { 'application_no': application_no, 'road_line_chainage_from': road_line_chainage_from, 'road_line_chainage_to': road_line_chainage_to, 'road_land_type': road_land_type, 'road_terrain': road_terrain, 'road_width': road_width, 'road_row': road_row, 'road_area_required': road_area_required, csrfmiddlewaretoken: csrf_token },
                            success: function (responseText) {
                                $('#anc_road_successMsg').html("Approach Road Details Added Successfully");
                                $('#anc_road_successMsg').show();
                                $('#anc_road_successMsg').delay(2000).fadeOut('slow');
                                setTimeout(function () {
                                    $('#anc_approach_road_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#anc_approach_road_details').html(responseText);
                                }, 2000);
                                setTimeout(function () {
                                    $('#anc_approach_road_form')[0].reset();
                                }, 2000);
                            }
                        });
                }
            }

            function populate_approach_road_details(record_id, application_no, line_chainage_from, line_chainage_to, land_type, terrain, road_width, row, area_required) {
                $('#edit_anc_app_record_id').val(record_id);
                $('#edit_anc_road_application_no').val(application_no);
                $('#edit_road_line_chainage_from').val(line_chainage_from);
                $('#edit_road_line_chainage_to').val(line_chainage_to);
                $('#edit_road_land_type').val(land_type);
                $('#edit_road_terrain').val(terrain);
                $('#edit_road_width').val(road_width);
                $('#edit_road_row').val(row);
                $('#edit_road_area_required').val(area_required);
                $('#edit_anc_approach_road_modal').modal('show');
            }

            function populate_delete_approach_road(record_id, application_no) {
                $('#delete_anc_road_record_id').val(record_id);
                $('#delete_anc_road_application_no').val(application_no);
                $('#delete_anc_approach_road_modal').modal('show');
            }

            function delete_anc_road_details() {
                let record_id = $('#delete_anc_road_record_id').val();
                let application_no = $('#delete_anc_road_application_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_anc_road_details/",
                        data: { 'record_id': record_id, 'application_no': application_no, csrfmiddlewaretoken: '{{ csrf_token }}' },
                        success: function (responseText) {
                            $('#delete_road_successMsg').html("Approach Road Details Deleted Successfully");
                            $('#delete_road_successMsg').show();
                            $('#delete_road_successMsg').delay(2000).fadeOut('slow');
                            setTimeout(function () {
                                $('#delete_anc_approach_road_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#anc_approach_road_details').html(responseText);
                            }, 2000);
                        }
                    });
            }

            function update_anc_road_details() {
                let record_id = $('#edit_anc_app_record_id').val();
                let application_no = $('#edit_anc_road_application_no').val();
                let line_chainage_from = $('#edit_road_line_chainage_from').val();
                let line_chainage_to = $('#edit_road_line_chainage_to').val();
                let land_type = $('#edit_road_land_type').val();
                let terrain = $('#edit_road_terrain').val();
                let road_width = $('#edit_road_width').val();
                let row = $('#edit_road_row').val();
                let area_required = $('#edit_road_area_required').val();

                if (line_chainage_from == "") {
                    $('#edit_road_line_chainage_fromErrorMsg').html("Enter Transmission line Chainage From");
                    $('#edit_road_line_chainage_fromErrorMsg').show();
                    $('#edit_road_line_chainage_fromErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (line_chainage_to == "") {
                    $('#edit_road_line_chainage_toErrorMsg').html("Enter Transmission line Chainage To");
                    $('#edit_road_line_chainage_toErrorMsg').show();
                    $('#edit_road_line_chainage_toErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (land_type == "") {
                    $('#edit_road_land_typeErrorMsg').html("Select One");
                    $('#edit_road_land_typeErrorMsg').show();
                    $('#edit_road_land_typeErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (terrain == "") {
                    $('#edit_road_terrainErrorMsg').html("Select One ");
                    $('#edit_road_terrainErrorMsg').show();
                    $('#edit_road_terrainErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (road_width == "") {
                    $('#edit_road_widthErrorMsg').html("Enter Type of Tower");
                    $('#edit_road_widthErrorMsg').show();
                    $('#edit_road_widthErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (row == "") {
                    $('#edit_road_rowErrorMsg').html("Enter Type of Tower");
                    $('#edit_road_roweErrorMsg').show();
                    $('#edit_road_rowErrorMsg').delay(2000).fadeOut('slow');
                }
                else if (area_required == "") {
                    $('#edit_road_area_requiredErrorMsg').html("Enter Area Required");
                    $('#edit_road_area_requiredErrorMsg').show();
                    $('#edit_road_area_requiredErrorMsg').delay(2000).fadeOut('slow');
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/update_anc_road_details/",
                            data: { 'record_id': record_id, 'application_no': application_no, 'line_chainage_from': line_chainage_from, 'line_chainage_to': line_chainage_to, 'land_type': land_type, 'terrain': terrain, 'road_width': road_width, 'row': row, 'area_required': area_required, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#edit_road_successMsg').html("Approach Road Details Updated Successfully");
                                $('#edit_road_successMsg').show();
                                $('#edit_road_successMsg').delay(2000).fadeOut('slow');
                                setTimeout(function () {
                                    $('#edit_anc_approach_road_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#anc_approach_road_details').html(responseText);
                                }, 2000);
                            }
                        });
                }
            }

            function check_dzong_throm(value) {
                if (value == "Dzongkhag") {
                    $('.dzongkhag').show();
                    $('.thromde').hide();
                }
                else {
                    $('.thromde').show();
                    $('.dzongkhag').hide();
                }
            }

            function check_excavated_muck(value) {
                if (value == "Yes") {
                    $('.dump_yard_details').show();
                }
                else {
                    $('.dump_yard_details').hide();
                }
            }

            function add_final_products_details() {
                let application_no = $('#application_no').val();
                let produce_name = $('#product_name').val();
                let quantity_annum = $('#quantity_annum').val();
                let storage_method = $('#storage_method').val();

                if (produce_name == "") {
                    $('#produce_nameErrorMsg').html("Enter Name of Produce");
                    $('#produce_nameErrorMsg').show();
                    $('#produce_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#produce_name').focus();
                }
                else if (quantity_annum == "") {
                    $('#quantity_annumErrorMsg').html("Enter Installed capacity/quantity per annum");
                    $('#quantity_annumErrorMsg').show();
                    $('#quantity_annumErrorMsg').delay(2000).fadeOut('slow');
                    $('#quantity_annum').focus();
                }
                else if (storage_method == "") {
                    $('#storage_methodErrorMsg').html("Enter Method of Storage");
                    $('#storage_methodErrorMsg').show();
                    $('#storage_methodErrorMsg').delay(2000).fadeOut('slow');
                    $('#storage_method').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/add_final_product_details/",
                            data: { 'application_no': application_no, 'produce_name': produce_name, 'quantity_annum': quantity_annum, 'storage_method': storage_method, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#final_products_SuccessMsg').html("Add Successful");
                                $('#final_products_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#final_products_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#final_products_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#final_products_div').html(responseText);
                                }, 2000);
                                $('#final_products_form')[0].reset();
                            }
                        });
                }
            }

            function edit_produce_populate(record_id, application_no, produce_name, qty, storage_method) {
                $('#edit_final_products_record_id').val(record_id)
                $('#edit_final_products_app_no').val(application_no)
                $('#edit_produce_name').val(produce_name);
                $('#edit_quantity_annum').val(qty);
                $('#edit_final_product_storage_method').val(storage_method);
                $('#edit_final_products_modal').modal('show');
            }

            function update_final_product_details() {
                let record_id = $('#edit_final_products_record_id').val();
                let application_no = $('#edit_final_products_app_no').val();
                let produce_name = $('#edit_produce_name').val();
                let quantity_annum = $('#edit_quantity_annum').val();
                let storage_method = $('#edit_final_product_storage_method').val();

                if (produce_name == "") {
                    $('#edit_produce_nameErrorMsg').html("Enter Name of Produce");
                    $('#edit_produce_nameErrorMsg').show();
                    $('#edit_produce_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_produce_name').focus();
                }
                else if (quantity_annum == "") {
                    $('#edit_final_product_qtyErrorMsg').html("Enter Installed capacity/quantity per annum");
                    $('#edit_final_product_qtyErrorMsg').show();
                    $('#edit_final_product_qtyErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_final_product_qty').focus();
                }
                else if (storage_method == "") {
                    $('#edit_final_product_storage_methodErrorMsg').html("Enter Method of Storage");
                    $('#edit_final_product_storage_methodErrorMsg').show();
                    $('#edit_final_product_storage_methodErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_final_product_storage_method').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/update_final_product_details/",
                            data: { 'application_no': application_no, 'record_id': record_id, 'produce_name': produce_name, 'quantity_annum': quantity_annum, 'storage_method': storage_method, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#edit_final_product_SuccessMsg').html("Update Successful");
                                $('#edit_final_product_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#edit_final_product_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#edit_final_products_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#final_products_div').html(responseText);
                                }, 2000);
                            }
                        });
                }
            }

            function populate_delete_produce(record_id, application_no) {
                $('#delete_final_product_record_id').val(record_id);
                $('#delete_final_product_app_no').val(application_no);
                $('#delete_final_product_modal').modal('show');
            }

            function delete_final_product_details() {
                let record_id = $('#delete_final_product_record_id').val();
                let application_no = $('#delete_final_product_app_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_final_product_details/",
                        data: { 'record_id': record_id, 'application_no': application_no, csrfmiddlewaretoken: '{{ csrf_token }}' },
                        success: function (responseText) {
                            $('#delete_final_product_SuccessMsg').html("Deleted Successfully");
                            $('#delete_final_product_SuccessMsg').show();
                            setTimeout(function () {
                                $('#delete_final_product_SuccessMsg').delay(2000).fadeOut('slow');
                            }, 2000);
                            setTimeout(function () {
                                $('#delete_final_product_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#final_products_div').html(responseText);
                            }, 2000);
                        }
                    });
            }

            function save_general_info(service) {
                $('.alert-danger').hide();

                let project_name = $('#project_name').val();
                let applicant_name = $('#applicant_name').val();
                let address = $('#address').val();
                let contact_no = $('#contact_no').val();
                let contact_no_length = contact_no.length;
                let email = $('#email').val();
                let industry_type = $('#industry_type').val();
                let establishment_type = $('#establishment_type').val();
                let industry_classification = $('#industry_classification').val();
                let dzongkhag_throm = $("input[name=dzongkhag_throm]:checked").length;
                let dzongkhag_throm_val = $("input[name=dzongkhag_throm]:checked").val();
                let thromde_id = $('#thromde_id').val();
                let dzongkhag_code = $('#dzongkhag').val();
                let gewog_code = $('#gewog').val();
                let village_code = $('#vil_chiwog').val();
                let project_site = $('#project_site').val();
                let industrial_area_acre = $('#industrial_area_acre').val();
                let state_reserve_forest_acre = $('#state_reserve_forest_acre').val();
                let private_area_acre = $('#private_area_acre').val();
                let others_area = $('#others_area').val();
                let others_area_acre = $('#others_area_acre').val();
                let total_build_up_area = $('#total_build_up_area').val();

                // Validation checks (same as before)
                if (project_name === "") {
                    showErrorAndFocus('#project_nameErrorMsg', 'Enter Name of Project', '#project_name');
                    return false;
                }
                // ... same validation logic ...
                else if (total_build_up_area == "" && service_name == 'TRA') {
                    showErrorAndFocus('#others_area_acreErrorMsg', 'Enter Others Area', '#others_area_acre');
                    return false;
                }
                else {
                    // Submit form via AJAX
                    $.ajax({
                        type: "POST",
                        url: "/save_general_info/",
                        data: $('#general_application_form').serialize(),
                        success: function (data) {
                            if (data.message == 'success') {
                                $('#successMsgText').text("Saved Successfully");
                                $('#application_form_successMsg').show();

                                setTimeout(function () {
                                    $('#application_form_successMsg').focus();

                                    $('html, body').animate({
                                        scrollTop: $('#application_form_successMsg').offset().top - 100
                                    }, 300);
                                }, 100);

                                setTimeout(function () {
                                    $('#application_form_successMsg').fadeOut('slow');
                                    $("#headingTwoBtn").removeAttr("disabled");
                                    $("#collapseTwo").addClass("show");
                                    $("#collapseOne").removeClass("show");
                                }, 3000);
                            }
                            else {
                                $('#errorMsgText').text(`Application Error: ${data.error}`);
                                $('#application_form_errorMsg').show();

                                setTimeout(function () {
                                    $('#application_form_errorMsg').focus();

                                    $('html, body').animate({
                                        scrollTop: $('#application_form_errorMsg').offset().top - 100
                                    }, 300);
                                }, 100);

                                setTimeout(function () {
                                    $('#application_form_errorMsg').fadeOut('slow');
                                }, 3000);
                            }
                        }
                    });
                }
            }

            // Show error and focus on the related input
            function showErrorAndFocus(errorElement, message, focusElement) {
                $(errorElement).html(message).show();

                setTimeout(function () {
                    const $focusTarget = $(focusElement);

                    if ($focusTarget.is(':input, select, textarea, button')) {
                        $focusTarget.focus();
                    }

                    $('html, body').animate({
                        scrollTop: $focusTarget.offset().top - 100
                    }, 300);
                }, 100);

                setTimeout(function () {
                    $(errorElement).fadeOut('slow');
                }, 3000);
            }

            function check_anc_other_crushing_unit() {
                if ($('#anc_other_crushing_unit').is(":checked")) {
                    $('.industry_application').show();
                }
                else {
                    $('.industry_application').hide();
                }
            }

            function check_anc_other_surface_collection() {
                if ($('#anc_other_surface_collection').is(":checked")) {
                    $('.forestry_application').show();
                }
                else {
                    $('.forestry_application').hide();
                }
            }

            function check_anc_other_general() {
                if ($('#anc_other_general').is(":checked") || $('#anc_other_mineral').is(":checked")) {
                    $('.general_application').show();
                    $('.mineral_application').show();
                }
                else if ($('#anc_other_general').is(":checked") && $('#anc_other_mineral').not(":checked")) {
                    $('.general_application').show();
                    $('.mineral_application').hide();
                }
                else if ($('#anc_other_general').not(":checked") && $('#anc_other_mineral').is(":checked")) {
                    $('.general_application').hide();
                    $('.mineral_application').show();
                }
                else if ($('#anc_other_general').not(":checked") && $('#anc_other_mineral').not(":checked")) {
                    $('.general_application').hide();
                    $('.mineral_application').hide();
                }
            }

            function get_total_area_acre() {
                let industrial_area_acre = $('#industrial_area_acre').val();
                let state_reserve_forest_acre = $('#state_reserve_forest_acre').val();
                let private_area_acre = $('#private_area_acre').val();
                let others_area_acre = $('#others_area_acre').val();
                let sum = 0;
                sum += parseFloat(industrial_area_acre) || 0;
                sum += parseFloat(state_reserve_forest_acre) || 0;
                sum += parseFloat(private_area_acre) || 0;
                sum += parseFloat(others_area_acre) || 0;

                $('#total_area_acre').val(sum);
            }

            function getCitizenDetails(cid) {
                $.ajax({
                    type: "GET",
                    url: "/check_cid_exists/",
                    data: { 'cid': cid },
                    success: function (data) {
                        if (data.count > 0) {
                            $('#cid').val("");
                            $('#applicant_name').val("");
                            $('#cidErrorMsg').html("CID Already Exists.Try With Another one");
                            $('#cidErrorMsg').show();
                            $('#cidErrorMsg').delay(2000).fadeOut('slow');
                        }
                        else {
                            const myObj = data.response;
                            if (myObj.citizendatas.citizendata == undefined) {
                                $('#cid').val("");
                                $('#cidErrorMsg').html("Invalid CID.Try With Another one");
                                $('#cidErrorMsg').show();
                                $('#cidErrorMsg').delay(2000).fadeOut('slow');
                            }
                            else {
                                var CitizenName = myObj.citizendatas.citizendata[0].Name
                                var dzongkhagName = myObj.citizendatas.citizendata[0].Dzongkhag_Name
                                var villageName = myObj.citizendatas.citizendata[0].Gewog_Name
                                var gewogName = myObj.citizendatas.citizendata[0].Village_Name
                                $('#applicant_name').val(CitizenName);
                            }
                        }
                    }
                });
            }

            function getGewog(dzongkhag_id) {
                $.ajax({
                    type: "GET",
                    url: "/load_gewog/",
                    data: { 'dzongkhag_id': dzongkhag_id },
                    success: function (data) {
                        console.log("Returned HTML:", data); // inspect this!
                        $('#gewog').html(data);
                    },
                    error: function (xhr, status, error) {
                        console.error("Error:", error);
                    }
                });
            }

            function getVillage(gewog_id) {
                $.ajax({
                    type: "GET",
                    url: "/load_village/",
                    data: { 'gewog_id': gewog_id },
                    success: function (data) {
                        $('#vil_chiwog').html(data);
                    }
                });
            }

            function calculate_road_area_required() {
                let road_line_chainage_from = $('#road_line_chainage_from').val();
                let road_line_chainage_to = $('#road_line_chainage_to').val();
                let road_row = $('#road_row').val();
                let sum = 0;
                let product = 0;

                sum += parseFloat(road_line_chainage_from) || 0;
                sum += parseFloat(road_line_chainage_to) || 0;
                product = parseFloat(sum) * parseFloat(road_row) || 0;

                $('#road_area_required').val(product);
            }

            function calculate_edit_road_area_required() {
                let road_line_chainage_from = $('#edit_road_line_chainage_from').val();
                let road_line_chainage_to = $('#edit_road_line_chainage_to').val();
                let road_row = $('#edit_road_row').val();
                let sum = 0;
                let product = 0;

                sum += parseFloat(road_line_chainage_from) || 0;
                sum += parseFloat(road_line_chainage_to) || 0;
                product = parseFloat(sum) * parseFloat(road_row) || 0;

                $('#edit_road_area_required').val(product);
            }

            function add_dumpyard_details() {
                let application_no = $('#application_no').val();
                let dumpyard_number = $('#dumpyard_number').val();
                let dumpyard_capacity = $('#dumpyard_capacity').val();
                let dumpyard_area = $('#dumpyard_area').val();
                let dumpyard_location = $('#dumpyard_location').val();

                if (dumpyard_number == "") {
                    $('#dumpyard_numberErrorMsg').html("Enter Dumpyard Number");
                    $('#dumpyard_numberErrorMsg').show();
                    $('#dumpyard_numberErrorMsg').delay(2000).fadeOut('slow');
                    $('#dumpyard_number').focus();
                }
                else if (dumpyard_capacity == "") {
                    $('#dumpyard_capacityErrorMsg').html("Enter Dumpyard Capacity");
                    $('#dumpyard_capacityErrorMsg').show();
                    $('#dumpyard_capacityErrorMsg').delay(2000).fadeOut('slow');
                    $('#dumpyard_capacity').focus();
                }
                else if (dumpyard_area == "") {
                    $('#dumpyard_areaErrorMsg').html("Enter Dumpyard Area");
                    $('#dumpyard_areaErrorMsg').show();
                    $('#dumpyard_areaErrorMsg').delay(2000).fadeOut('slow');
                    $('#dumpyard_area').focus();
                }
                else if (dumpyard_location == "") {
                    $('#dumpyard_locationErrorMsg').html("Enter Dumpyard Location");
                    $('#dumpyard_locationErrorMsg').show();
                    $('#dumpyard_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#dumpyard_location').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/add_dumpyard_details/",
                            data: { 'application_no': application_no, 'dumpyard_number': dumpyard_number, 'dumpyard_capacity': dumpyard_capacity, 'dumpyard_area': dumpyard_area, 'dumpyard_location': dumpyard_location, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#dumpyard_SuccessMsg').html("Add Successful");
                                $('#dumpyard_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#dumpyard_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#dumyard_details_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#dump_yard_details_div').html(responseText);
                                }, 2000);
                                $('#dumyard_details_form')[0].reset();
                            }
                        });
                }
            }

            function populate_dumpyard_data(record_id, application_no, dumpyard_number, dumpyard_capacity, dumpyard_area, dumpyard_location) {
                $('#dumpyard_record_id').val(record_id);
                $('#dumpyard_application_no').val(application_no);
                $('#edit_dumpyard_number').val(dumpyard_number);
                $('#edit_dumpyard_capacity').val(dumpyard_capacity);
                $('#edit_dumpyard_area').val(dumpyard_area);
                $('#edit_dumpyard_location').val(dumpyard_location);

                $('#edit_dumyard_details_modal').modal('show');
            }

            function update_dumpyard_details() {
                let record_id = $('#dumpyard_record_id').val();
                let application_no = $('#dumpyard_application_no').val();
                let dumpyard_number = $('#edit_dumpyard_number').val();
                let dumpyard_capacity = $('#edit_dumpyard_capacity').val();
                let dumpyard_area = $('#edit_dumpyard_area').val();
                let dumpyard_location = $('#edit_dumpyard_location').val();

                if (dumpyard_number == "") {
                    $('#edit_dumpyard_numberErrorMsg').html("Enter Dumpyard Number");
                    $('#edit_dumpyard_numberErrorMsg').show();
                    $('#edit_dumpyard_numberErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_dumpyard_number').focus();
                }
                else if (dumpyard_capacity == "") {
                    $('#edit_dumpyard_capacityErrorMsg').html("Enter Dumpyard Capacity");
                    $('#edit_dumpyard_capacityErrorMsg').show();
                    $('#edit_dumpyard_capacityErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_dumpyard_capacity').focus();
                }
                else if (dumpyard_area == "") {
                    $('#edit_dumpyard_areaErrorMsg').html("Enter Dumpyard Area");
                    $('#edit_dumpyard_areaErrorMsg').show();
                    $('#edit_dumpyard_areaErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_dumpyard_area').focus();
                }
                else if (dumpyard_location == "") {
                    $('#edit_dumpyard_locationErrorMsg').html("Enter Dumpyard Location");
                    $('#edit_dumpyard_locationErrorMsg').show();
                    $('#edit_dumpyard_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#edit_dumpyard_location').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/update_dumpyard_details/",
                            data: { 'record_id': record_id, 'application_no': application_no, 'dumpyard_number': dumpyard_number, 'dumpyard_capacity': dumpyard_capacity, 'dumpyard_area': dumpyard_area, 'dumpyard_location': dumpyard_location, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#edit_dumpyard_SuccessMsg').html("Update Successful");
                                $('#edit_dumpyard_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#edit_dumpyard_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#edit_dumyard_details_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#dump_yard_details_div').html(responseText);
                                }, 2000);
                            }
                        });
                }
            }

            function populate_delete_dumpyard_data(record_id, application_no) {
                $('#delete_dumpyard_record_id').val(record_id);
                $('#delete_dumpyard_application_no').val(application_no);
                $('#delete_dumyard_details_modal').modal('show');
            }

            function delete_dumpyard_details() {
                let record_id = $('#delete_dumpyard_record_id').val();
                let application_no = $('#delete_dumpyard_application_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_dumpyard_details/",
                        data: { 'record_id': record_id, 'application_no': application_no, csrfmiddlewaretoken: '{{ csrf_token }}' },
                        success: function (responseText) {
                            $('#delete_dumpyard_SuccessMsg').html("Delete Successful");
                            $('#delete_dumpyard_SuccessMsg').show();
                            setTimeout(function () {
                                $('#delete_dumpyard_SuccessMsg').delay(2000).fadeOut('slow');
                            }, 2000);
                            setTimeout(function () {
                                $('#delete_dumyard_details_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#dump_yard_details_div').html(responseText);
                            }, 2000);
                        }
                    });
            }

            function check_terms() {
                if ($("#ec_terms").prop('checked') == true) {
                    $('#gen_submit_btn').show();
                }
                else {
                    $('#gen_submit_btn').hide();
                }
            }

            function save_water_requirement_details() {
                // Hide all error messages first
                $('.alert-danger').hide();

                // Get radio button value
                const waterRequired = $("input[name=water_required]:checked").val() === 'Yes';
                const waterRequiredChecked = $("input[name=water_required]:checked").length > 0;

                // Define validation rules
                const validations = [
                    // Basic validations (always required)
                    {
                        condition: $('#energy_source').val() === "",
                        errorId: 'energy_sourceErrorMsg',
                        focusId: 'energy_source',
                        message: 'Select Source Of Energy.'
                    },
                    {
                        condition: !waterRequiredChecked,
                        errorId: 'water_requiredErrorMsg',
                        focusId: 'water_required',
                        message: 'Please Select One.'
                    },

                    // Conditional validations (only if water is required)
                    {
                        condition: waterRequired && $('#water_raw_material_source').val() === "",
                        errorId: 'water_raw_material_sourceErrorMsg',
                        focusId: 'water_raw_material_source',
                        message: 'Select raw material water source.'
                    },
                    {
                        condition: waterRequired && $('#water_raw_material_qty_day').val() === "",
                        errorId: 'water_raw_material_qty_dayErrorMsg',
                        focusId: 'water_raw_material_qty_day',
                        message: 'Enter raw material water quantity per day.'
                    },
                    {
                        condition: waterRequired && $('#water_raw_material_recycle_day').val() === "",
                        errorId: 'water_raw_material_recycle_dayErrorMsg',
                        focusId: 'water_raw_material_recycle_day',
                        message: 'Enter raw material water recycled per day.'
                    },
                    // Add similar validations for other water types...
                    {
                        condition: waterRequired && $('#water_cleaning_source').val() === "",
                        errorId: 'water_cleaning_sourceErrorMsg',
                        focusId: 'water_cleaning_source',
                        message: 'Select cleaning water source.'
                    },
                    {
                        condition: waterRequired && $('#water_cleaning_qty_day').val() === "",
                        errorId: 'water_cleaning_qty_dayErrorMsg',
                        focusId: 'water_cleaning_qty_day',
                        message: 'Enter cleaning water quantity per day.'
                    },
                    {
                        condition: waterRequired && $('#water_cleaning_recycle_day').val() === "",
                        errorId: 'water_cleaning_recycle_dayErrorMsg',
                        focusId: 'water_cleaning_recycle_day',
                        message: 'Enter cleaning water recycled per day.'
                    },
                    // Continue with other water type validations...
                    {
                        condition: waterRequired && $('#total_water_consumption').val() === "",
                        errorId: 'total_water_consumptionErrorMsg',
                        focusId: 'total_water_consumption',
                        message: 'Enter total water consumption.'
                    },
                    {
                        condition: waterRequired && $('#total_water_recycled').val() === "",
                        errorId: 'total_water_recycledErrorMsg',
                        focusId: 'total_water_recycled',
                        message: 'Enter total water recycled.'
                    }
                ];

                // Check all validations
                for (const validation of validations) {
                    if (validation.condition) {
                        showErrorAndFocus(validation.errorId, validation.message, validation.focusId);
                        return false;
                    }
                }

                // If all validations pass, submit the form
                submitWaterRequirementForm();
            }

            function submitWaterRequirementForm() {
                $.ajax({
                    type: "POST",
                    url: "/save_water_requirement_details/",
                    data: $('#water_requirement_form').serialize(),
                    success: function (data) {
                        if (data.message === 'success') {
                            showSuccessMessage(
                                'water_requirement_application_successMsg',
                                'Saved Successfully',
                                function () {
                                    $("#headingFiveBtn").removeAttr("disabled");
                                    $("#collapseFive").addClass("show");
                                    $("#collapseFour").removeClass("show");
                                }
                            );
                        } else {
                            showErrorMessage(
                                'water_requirement_application_errorMsg',
                                data.error || 'Application Error'
                            );
                        }
                    },
                    error: function (xhr, status, error) {
                        showErrorMessage(
                            'water_requirement_application_errorMsg',
                            `Request Error: ${error}`
                        );
                    }
                });
            }


            function check_construction_substation(value) {

                if (value == "Yes") {
                    $('.construction_substation_details').show();
                }
                else {
                    $('.construction_substation_details').hide();
                }
            }


            function save_power_line() {
                $('#power_line_successMsg').html("Saved Successfully");
                $('#power_line_successMsg').show();
                setTimeout(function () {
                    $('#power_line_successMsg').delay(2000).fadeOut('slow');
                }, 2000);
                setTimeout(function () {
                    $("#collapseFourBtn").removeAttr("disabled");
                    $("#collapseFour").addClass("show");
                    $("#collapseSix").removeClass("show");
                }, 2000);
            }

            function check_excavated_muck(value) {
                if (value == "Yes") {
                    $('.dump_yard_details').show();
                }
                else {
                    $('.dump_yard_details').hide();
                }
            }

            function check_tansmission_water_radio(value) {
                if (value == 'Yes') {
                    $('.general_water_details').show();
                }
                else {
                    $('.general_water_details').hide();
                }
            }


            function save_iee_application() {
                let project_name = $('#project_name').val();
                let project_category = $('#project_category').val();
                let industry_type = $('#industry_type').val();
                let establishment_name = $('#establishment_name').val();
                let industry_classification = $('#industry_classification').val();
                let dzongkhag_code = $('#dzo_throm').val();
                let gewog_code = $('#gewog').val();
                let village_code = $('#vil_chiwog').val();
                let location_name = $('#location_name').val();
                let industrial_area_acre = $('#industrial_area_acre').val();
                let state_reserve_forest_acre = $('#state_reserve_forest_acre').val();
                let private_area_acre = $('#private_area_acre').val();
                let others_area = $('#others_area').val();
                let others_area_acre = $('#others_area_acre').val();
                let green_area_acre = $('#green_area_acre').val();
                let production_process_flow = $('#production_process_flow').val();
                let project_objective = $('#project_objective').val();
                let project_no_of_workers = $('#project_no_of_workers').val();
                let project_cost = $('#project_cost').val();
                let project_duration = $('#project_duration').val();

                if (project_name == "") {
                    $('#project_nameErrorMsg').html("Enter Name of Project");
                    $('#project_nameErrorMsg').show();
                    $('#project_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_name').focus();
                }
                else if (project_category == "") {
                    $('#project_categoryErrorMsg').html("Enter Business Type");
                    $('#project_categoryErrorMsg').show();
                    $('#project_categoryErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_category').focus();
                }
                else if (industry_type == "") {
                    $('#industry_typeErrorMsg').html("Enter Industry Type");
                    $('#industry_typeErrorMsg').show();
                    $('#industry_typeErrorMsg').delay(2000).fadeOut('slow');
                    $('#industry_type').focus();
                }
                else if (establishment_name == "") {
                    $('#establishment_nameErrorMsg').html("Enter Establishment Name");
                    $('#establishment_nameErrorMsg').show();
                    $('#establishment_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#establishment_name').focus();
                }
                else if (industry_classification == "") {
                    $('#industry_classificationErrorMsg').html("Enter Classification of Industry");
                    $('#industry_classificationErrorMsg').show();
                    $('#industry_classificationErrorMsg').delay(2000).fadeOut('slow');
                    $('#industry_classification').focus();
                }
                else if (dzongkhag_code == "") {
                    $('#dzo_thromErrorMsg').html("Select Dzongkhag");
                    $('#dzo_thromErrorMsg').show();
                    $('#dzo_thromErrorMsg').delay(2000).fadeOut('slow');
                    $('#dzo_throm').focus();
                }
                else if (gewog_code == "") {
                    $('#gewogErrorMsg').html("Select Gewog");
                    $('#gewogErrorMsg').show();
                    $('#gewogErrorMsg').delay(2000).fadeOut('slow');
                    $('#gewog').focus();
                }
                else if (village_code == "") {
                    $('#vil_chiwogErrorMsg').html("Select Village");
                    $('#vil_chiwogErrorMsg').show();
                    $('#vil_chiwogErrorMsg').delay(2000).fadeOut('slow');
                    $('#vil_chiwog').focus();
                }
                else if (location_name == "") {
                    $('#location_nameErrorMsg').html("Enter Name of The Particular Project Site");
                    $('#location_nameErrorMsg').show();
                    $('#location_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#location_name').focus();
                }
                else if (industrial_area_acre == "") {
                    $('#industrial_area_acreErrorMsg').html("Enter Industrial Area/Estate/Park/Special Economic Zone (SEZ)");
                    $('#industrial_area_acreErrorMsg').show();
                    $('#industrial_area_acreErrorMsg').delay(2000).fadeOut('slow');
                    $('#industrial_area_acre').focus();
                }
                else if (industrial_area_acre == "") {
                    $('#industrial_area_acreErrorMsg').html("Enter Industrial Area/Estate/Park/Special Economic Zone (SEZ)");
                    $('#industrial_area_acreErrorMsg').show();
                    $('#industrial_area_acreErrorMsg').delay(2000).fadeOut('slow');
                    $('#industrial_area_acre').focus();
                }
                else if (state_reserve_forest_acre == "") {
                    $('#state_reserve_forest_acreErrorMsg').html("Enter State Reserve Forest Area");
                    $('#state_reserve_forest_acreErrorMsg').show();
                    $('#state_reserve_forest_acreErrorMsg').delay(2000).fadeOut('slow');
                    $('#state_reserve_forest_acre').focus();
                }
                else if (private_area_acre == "") {
                    $('#private_area_acreErrorMsg').html("Enter Private Area");
                    $('#private_area_acreErrorMsg').show();
                    $('#private_area_acreErrorMsg').delay(2000).fadeOut('slow');
                    $('#private_area_acre').focus();
                }
                else if (others_area != "NA" || others_area != "" && others_area_acre == "") {
                    $('#others_area_acreErrorMsg').html("Enter Others Area");
                    $('#others_area_acreErrorMsg').show();
                    $('#others_area_acreErrorMsg').delay(2000).fadeOut('slow');
                    $('#others_area_acre').focus();
                }
                else if (green_area_acre == "") {
                    $('#green_area_acreErrorMsg').html("Enter Total Green Space");
                    $('#green_area_acreErrorMsg').show();
                    $('#green_area_acreErrorMsg').delay(2000).fadeOut('slow');
                    $('#green_area_acre').focus();
                }
                else if (production_process_flow == "") {
                    $('#production_process_flowErrorMsg').html("Enter Brief Description of Production and Process Flow");
                    $('#production_process_flowErrorMsg').show();
                    $('#production_process_flowErrorMsg').delay(2000).fadeOut('slow');
                    $('#production_process_flow').focus();
                }
                else if (project_objective == "") {
                    $('#project_objectiveErrorMsg').html("Enter Project Objective");
                    $('#project_objectiveErrorMsg').show();
                    $('#project_objectiveErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_objective').focus();
                }
                else if (project_no_of_workers == "") {
                    $('#project_no_of_workersErrorMsg').html("Enter Project Objective");
                    $('#project_no_of_workersErrorMsg').show();
                    $('#project_no_of_workersErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_no_of_workers').focus();
                }
                else if (project_cost == "") {
                    $('#project_costErrorMsg').html("Enter Project Cost");
                    $('#project_costErrorMsg').show();
                    $('#project_costErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_cost').focus();
                }
                else if (project_duration == "") {
                    $('#project_durationErrorMsg').html("Enter Project Duration");
                    $('#project_durationErrorMsg').show();
                    $('#project_durationErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_duration').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_iee_application/",
                            data: $('#iee_application_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#application_form_successMsg').html("Saved Successfully");
                                    $('#application_form_successMsg').show();
                                    $('#application_form_successMsg').focus();
                                    setTimeout(function () {
                                        $('#application_form_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#headingTwoBtn").removeAttr("disabled");
                                        $("#collapseTwo").addClass("show");
                                        $("#collapseOne").removeClass("show");
                                        $('#proposed_location_justification').focus();
                                    }, 2000);
                                }
                                else {
                                    $('#application_form_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#application_form_errorMsg').show();
                                    $('#application_form_errorMsg').focus();

                                    setTimeout(function () {
                                        $('#application_form_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }

            function check_industry_radio(value) {
                if (value == 'Yes') {
                    $('.industry_water_details').show();
                }
                else {
                    $('.industry_water_details').hide();
                }
            }

            function save_effluent_details() {
                let en_waste_water_generate = $("input[name=en_waste_water_generate]:checked").length;
                let en_waste_water_generate_value = $("input[name=en_waste_water_generate]:checked").val();
                let waste_water_nh3n_source = $('#waste_water_nh3n_source').val();
                let waste_water_nh3n_discharge = $('#waste_water_nh3n_discharge').val();
                let waste_water_nh3n_treatment = $('#waste_water_nh3n_treatment').val();
                let waste_water_nh3n_name_location = $('#waste_water_nh3n_name_location').val();
                let waste_water_arsenic_source = $('#waste_water_arsenic_source').val();
                let waste_water_arsenic_discharge = $('#waste_water_arsenic_discharge').val();
                let waste_water_arsenic_treatment = $('#waste_water_arsenic_treatment').val();
                let waste_water_arsenic_name_location = $('#waste_water_arsenic_name_location').val();
                let waste_water_bod_source = $('#waste_water_bod_source').val();
                let waste_water_bod_discharge = $('#waste_water_bod_discharge').val();
                let waste_water_bod_treatment = $('#waste_water_bod_treatment').val();
                let waste_water_bod_name_location = $('#waste_water_bod_name_location').val();
                let waste_water_boron_source = $('#waste_water_boron_source').val();
                let waste_water_boron_discharge = $('#waste_water_boron_discharge').val();
                let waste_water_boron_treatment = $('#waste_water_boron_treatment').val();
                let waste_water_boron_name_location = $('#waste_water_boron_name_location').val();
                let waste_water_cadmium_source = $('#waste_water_cadmium_source').val();
                let waste_water_cadmium_discharge = $('#waste_water_cadmium_discharge').val();
                let waste_water_cadmium_treatment = $('#waste_water_cadmium_treatment').val();
                let waste_water_cadmium_name_location = $('#waste_water_cadmium_name_location').val();
                let waste_water_cod_source = $('#waste_water_cod_source').val();
                let waste_water_cod_discharge = $('#waste_water_cod_discharge').val();
                let waste_water_cod_treatment = $('#waste_water_cod_treatment').val();
                let waste_water_cod_name_location = $('#waste_water_cod_name_location').val();
                let waste_water_cloride_source = $('#waste_water_cloride_source').val();
                let waste_water_cloride_discharge = $('#waste_water_cloride_discharge').val();
                let waste_water_cloride_treatment = $('#waste_water_cloride_treatment').val();
                let waste_water_cloride_name_location = $('#waste_water_cloride_name_location').val();
                let waste_water_chromium_source = $('#waste_water_chromium_source').val();
                let waste_water_chromium_discharge = $('#waste_water_chromium_discharge').val();
                let waste_water_chromium_treatment = $('#waste_water_chromium_treatment').val();
                let waste_water_chromium_name_location = $('#waste_water_chromium_name_location').val();
                let waste_water_chromium_hex_source = $('#waste_water_chromium_hex_source').val();
                let waste_water_chromium_hex_discharge = $('#waste_water_chromium_hex_discharge').val();
                let waste_water_chromium_hex_treatment = $('#waste_water_chromium_hex_treatment').val();
                let waste_water_chromium_hex_name_location = $('#waste_water_chromium_hex_name_location').val();
                let waste_water_copper_source = $('#waste_water_copper_source').val();
                let waste_water_copper_discharge = $('#waste_water_copper_discharge').val();
                let waste_water_copper_treatment = $('#waste_water_copper_treatment').val();
                let waste_water_copper_name_location = $('#waste_water_copper_name_location').val();
                let waste_water_cyanide_source = $('#waste_water_cyanide_source').val();
                let waste_water_cyanide_discharge = $('#waste_water_cyanide_discharge').val();
                let waste_water_cyanide_treatment = $('#waste_water_cyanide_treatment').val();
                let waste_water_cyanide_name_location = $('#waste_water_cyanide_name_location').val();
                let waste_water_floride_source = $('#waste_water_floride_source').val();
                let waste_water_floride_discharge = $('#waste_water_floride_discharge').val();
                let waste_water_floride_treatment = $('#waste_water_floride_treatment').val();
                let waste_water_floride_name_location = $('#waste_water_floride_name_location').val();
                let waste_water_phosphate_source = $('#waste_water_phosphate_source').val();
                let waste_water_phosphate_discharge = $('#waste_water_phosphate_discharge').val();
                let waste_water_phosphate_treatment = $('#waste_water_phosphate_treatment').val();
                let waste_water_phosphate_name_location = $('#waste_water_phosphate_name_location').val();
                let waste_water_nitrate_source = $('#waste_water_nitrate_source').val();
                let waste_water_nitrate_discharge = $('#waste_water_nitrate_discharge').val();
                let waste_water_nitrate_treatment = $('#waste_water_nitrate_treatment').val();
                let waste_water_nitrate_name_location = $('#waste_water_nitrate_name_location').val();
                let waste_water_iron_source = $('#waste_water_iron_source').val();
                let waste_water_iron_discharge = $('#waste_water_iron_discharge').val();
                let waste_water_iron_treatment = $('#waste_water_iron_treatment').val();
                let waste_water_iron_name_location = $('#waste_water_iron_name_location').val();
                let waste_water_lead_source = $('#waste_water_lead_source').val();
                let waste_water_lead_discharge = $('#waste_water_lead_discharge').val();
                let waste_water_lead_treatment = $('#waste_water_lead_treatment').val();
                let waste_water_lead_name_location = $('#waste_water_lead_name_location').val();
                let waste_water_manganese_source = $('#waste_water_manganese_source').val();
                let waste_water_manganese_discharge = $('#waste_water_manganese_discharge').val();
                let waste_water_manganese_treatment = $('#waste_water_manganese_treatment').val();
                let waste_water_manganese_name_location = $('#waste_water_manganese_name_location').val();
                let waste_water_mercury_source = $('#waste_water_mercury_source').val();
                let waste_water_mercury_discharge = $('#waste_water_mercury_discharge').val();
                let waste_water_mercury_treatment = $('#waste_water_mercury_treatment').val();
                let waste_water_mercury_name_location = $('#waste_water_mercury_name_location').val();
                let waste_water_nickel_source = $('#waste_water_nickel_source').val();
                let waste_water_nickel_discharge = $('#waste_water_nickel_discharge').val();
                let waste_water_nickel_treatment = $('#waste_water_nickel_treatment').val();
                let waste_water_nickel_name_location = $('#waste_water_nickel_name_location').val();
                let waste_water_oil_source = $('#waste_water_oil_source').val();
                let waste_water_oil_discharge = $('#waste_water_oil_discharge').val();
                let waste_water_oil_treatment = $('#waste_water_oil_treatment').val();
                let waste_water_oil_name_location = $('#waste_water_oil_name_location').val();
                let waste_water_ph_source = $('#waste_water_ph_source').val();
                let waste_water_ph_discharge = $('#waste_water_ph_discharge').val();
                let waste_water_ph_treatment = $('#waste_water_ph_treatment').val();
                let waste_water_ph_name_location = $('#waste_water_ph_name_location').val();
                let waste_water_phenolic_source = $('#waste_water_phenolic_source').val();
                let waste_water_phenolic_discharge = $('#waste_water_phenolic_discharge').val();
                let waste_water_phenolic_treatment = $('#waste_water_phenolic_treatment').val();
                let waste_water_phenolic_name_location = $('#waste_water_phenolic_name_location').val();
                let waste_water_selenium_source = $('#waste_water_selenium_source').val();
                let waste_water_selenium_discharge = $('#waste_water_selenium_discharge').val();
                let waste_water_selenium_treatment = $('#waste_water_selenium_treatment').val();
                let waste_water_selenium_name_location = $('#waste_water_selenium_name_location').val();
                let waste_water_so4_source = $('#waste_water_so4_source').val();
                let waste_water_so4_discharge = $('#waste_water_so4_discharge').val();
                let waste_water_so4_treatment = $('#waste_water_so4_treatment').val();
                let waste_water_so4_name_location = $('#waste_water_so4_name_location').val();
                let waste_water_s_source = $('#waste_water_s_source').val();
                let waste_water_s_discharge = $('#waste_water_s_discharge').val();
                let waste_water_s_treatment = $('#waste_water_s_treatment').val();
                let waste_water_s_name_location = $('#waste_water_s_name_location').val();
                let waste_water_tds_source = $('#waste_water_tds_source').val();
                let waste_water_tds_discharge = $('#waste_water_tds_discharge').val();
                let waste_water_tds_treatment = $('#waste_water_tds_treatment').val();
                let waste_water_tds_name_location = $('#waste_water_tds_name_location').val();
                let waste_water_tss_source = $('#waste_water_tss_source').val();
                let waste_water_tss_discharge = $('#waste_water_tss_discharge').val();
                let waste_water_tss_treatment = $('#waste_water_tss_treatment').val();
                let waste_water_tss_name_location = $('#waste_water_tss_name_location').val();
                let waste_water_temp_source = $('#waste_water_temp_source').val();
                let waste_water_temp_discharge = $('#waste_water_temp_discharge').val();
                let waste_water_temp_treatment = $('#waste_water_temp_treatment').val();
                let waste_water_temp_name_location = $('#waste_water_temp_name_location').val();
                let waste_water_tkn_source = $('#waste_water_tkn_source').val();
                let waste_water_tkn_discharge = $('#waste_water_tkn_discharge').val();
                let waste_water_tkn_treatment = $('#waste_water_tkn_treatment').val();
                let waste_water_tkn_name_location = $('#waste_water_tkn_name_location').val();
                let waste_water_residual_cloride_source = $('#waste_water_residual_cloride_source').val();
                let waste_water_residual_cloride_discharge = $('#waste_water_residual_cloride_discharge').val();
                let waste_water_residual_cloride_treatment = $('#waste_water_residual_cloride_treatment').val();
                let waste_water_residual_cloride_name_location = $('#waste_water_residual_cloride_name_location').val();
                let waste_water_zinc_source = $('#waste_water_zinc_source').val();
                let waste_water_zinc_discharge = $('#waste_water_zinc_discharge').val();
                let waste_water_zinc_treatment = $('#waste_water_zinc_treatment').val();
                let waste_water_zinc_name_location = $('#waste_water_zinc_name_location').val();
                let waste_water_ammonia_source = $('#waste_water_ammonia_source').val();
                let waste_water_ammonia_discharge = $('#waste_water_ammonia_discharge').val();
                let waste_water_ammonia_treatment = $('#waste_water_ammonia_treatment').val();
                let waste_water_ammonia_name_location = $('#waste_water_ammonia_name_location').val();
                let waste_water_colour_source = $('#waste_water_colour_source').val();
                let waste_water_colour_discharge = $('#waste_water_colour_discharge').val();
                let waste_water_colour_treatment = $('#waste_water_colour_treatment').val();
                let waste_water_colour_name_location = $('#waste_water_colour_name_location').val();


                if (en_waste_water_generate < 1) {
                    $('#en_waste_water_generateErrorMsg').html("Please Select One.");
                    $('#en_waste_water_generateErrorMsg').show();
                    $('#en_waste_water_generateErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_waste_water_generate').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nh3n_source == "") {
                    $('#waste_water_nh3n_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nh3n_sourceErrorMsg').show();
                    $('#waste_water_nh3n_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nh3n_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nh3n_discharge == "") {
                    $('#waste_water_nh3n_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nh3n_dischargeErrorMsg').show();
                    $('#waste_water_nh3n_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nh3n_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nh3n_treatment == "") {
                    $('#waste_water_nh3n_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nh3n_treatmentErrorMsg').show();
                    $('#waste_water_nh3n_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nh3n_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nh3n_name_location == "") {
                    $('#waste_water_nh3n_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nh3n_name_locationErrorMsg').show();
                    $('#waste_water_nh3n_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nh3n_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_arsenic_source == "") {
                    $('#waste_water_arsenic_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_arsenic_sourceErrorMsg').show();
                    $('#waste_water_arsenic_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_arsenic_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_arsenic_discharge == "") {
                    $('#waste_water_arsenic_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_arsenic_dischargeErrorMsg').show();
                    $('#waste_water_arsenic_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_arsenic_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_arsenic_treatment == "") {
                    $('#waste_water_arsenic_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_arsenic_treatmentErrorMsg').show();
                    $('#waste_water_arsenic_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_arsenic_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_arsenic_name_location == "") {
                    $('#waste_water_arsenic_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_arsenic_name_locationErrorMsg').show();
                    $('#waste_water_arsenic_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_arsenic_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_bod_source == "") {
                    $('#waste_water_bod_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_bod_sourceErrorMsg').show();
                    $('#waste_water_bod_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_bod_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_bod_discharge == "") {
                    $('#waste_water_bod_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_bod_dischargeErrorMsg').show();
                    $('#waste_water_bod_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_bod_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_bod_treatment == "") {
                    $('#waste_water_bod_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_bod_treatmentErrorMsg').show();
                    $('#waste_water_bod_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_bod_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_bod_name_location == "") {
                    $('#waste_water_bod_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_bod_name_locationErrorMsg').show();
                    $('#waste_water_bod_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_bod_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_boron_source == "") {
                    $('#waste_water_boron_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_boron_sourceErrorMsg').show();
                    $('#waste_water_boron_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_boron_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_boron_discharge == "") {
                    $('#waste_water_boron_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_boron_dischargeErrorMsg').show();
                    $('#waste_water_boron_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_boron_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_boron_treatment == "") {
                    $('#waste_water_boron_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_boron_treatmentErrorMsg').show();
                    $('#waste_water_boron_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_boron_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_boron_name_location == "") {
                    $('#waste_water_boron_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_boron_name_locationErrorMsg').show();
                    $('#waste_water_boron_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_boron_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cadmium_source == "") {
                    $('#waste_water_cadmium_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cadmium_sourceErrorMsg').show();
                    $('#waste_water_cadmium_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cadmium_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cadmium_discharge == "") {
                    $('#waste_water_cadmium_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cadmium_dischargeErrorMsg').show();
                    $('#waste_water_cadmium_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cadmium_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cadmium_treatment == "") {
                    $('#waste_water_cadmium_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cadmium_treatmentErrorMsg').show();
                    $('#waste_water_cadmium_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cadmium_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cadmium_name_location == "") {
                    $('#waste_water_cadmium_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cadmium_name_locationErrorMsg').show();
                    $('#waste_water_cadmium_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cadmium_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cod_source == "") {
                    $('#waste_water_cod_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cod_sourceErrorMsg').show();
                    $('#waste_water_cod_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cod_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cod_discharge == "") {
                    $('#waste_water_cod_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cod_dischargeErrorMsg').show();
                    $('#waste_water_cod_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cod_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cod_treatment == "") {
                    $('#waste_water_cod_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cod_treatmentErrorMsg').show();
                    $('#waste_water_cod_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cod_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cod_name_location == "") {
                    $('#waste_water_cod_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cod_name_locationErrorMsg').show();
                    $('#waste_water_cod_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cod_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cloride_source == "") {
                    $('#waste_water_cloride_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cloride_sourceErrorMsg').show();
                    $('#waste_water_cloride_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cloride_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cloride_discharge == "") {
                    $('#waste_water_cloride_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cloride_dischargeErrorMsg').show();
                    $('#waste_water_cloride_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cloride_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cloride_treatment == "") {
                    $('#waste_water_cloride_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cloride_treatmentErrorMsg').show();
                    $('#waste_water_cloride_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cloride_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cloride_name_location == "") {
                    $('#waste_water_cloride_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cloride_name_locationErrorMsg').show();
                    $('#waste_water_cloride_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cloride_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_source == "") {
                    $('#waste_water_chromium_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_sourceErrorMsg').show();
                    $('#waste_water_chromium_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_discharge == "") {
                    $('#waste_water_chromium_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_dischargeErrorMsg').show();
                    $('#waste_water_chromium_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_treatment == "") {
                    $('#waste_water_chromium_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_treatmentErrorMsg').show();
                    $('#waste_water_chromium_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_name_location == "") {
                    $('#waste_water_chromium_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_name_locationErrorMsg').show();
                    $('#waste_water_chromium_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_hex_source == "") {
                    $('#waste_water_chromium_hex_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_hex_sourceErrorMsg').show();
                    $('#waste_water_chromium_hex_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_hex_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_hex_discharge == "") {
                    $('#waste_water_chromium_hex_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_hex_dischargeErrorMsg').show();
                    $('#waste_water_chromium_hex_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_hex_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_hex_treatment == "") {
                    $('#waste_water_chromium_hex_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_hex_treatmentErrorMsg').show();
                    $('#waste_water_chromium_hex_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_hex_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_chromium_hex_name_location == "") {
                    $('#waste_water_chromium_hex_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_chromium_hex_name_locationErrorMsg').show();
                    $('#waste_water_chromium_hex_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_chromium_hex_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_copper_source == "") {
                    $('#waste_water_copper_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_copper_sourceErrorMsg').show();
                    $('#waste_water_copper_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_copper_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_copper_discharge == "") {
                    $('#waste_water_copper_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_copper_dischargeErrorMsg').show();
                    $('#waste_water_copper_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_copper_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_copper_treatment == "") {
                    $('#waste_water_copper_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_copper_treatmentErrorMsg').show();
                    $('#waste_water_copper_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_copper_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_copper_name_location == "") {
                    $('#waste_water_copper_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_copper_name_locationErrorMsg').show();
                    $('#waste_water_copper_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_copper_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cyanide_source == "") {
                    $('#waste_water_cyanide_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cyanide_sourceErrorMsg').show();
                    $('#waste_water_cyanide_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cyanide_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cyanide_discharge == "") {
                    $('#waste_water_cyanide_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cyanide_dischargeErrorMsg').show();
                    $('#waste_water_cyanide_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cyanide_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cyanide_treatment == "") {
                    $('#waste_water_cyanide_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cyanide_treatmentErrorMsg').show();
                    $('#waste_water_cyanide_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cyanide_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_cyanide_name_location == "") {
                    $('#waste_water_cyanide_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_cyanide_name_locationErrorMsg').show();
                    $('#waste_water_cyanide_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_cyanide_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_floride_source == "") {
                    $('#waste_water_floride_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_floride_sourceErrorMsg').show();
                    $('#waste_water_floride_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_floride_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_floride_discharge == "") {
                    $('#waste_water_floride_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_floride_dischargeErrorMsg').show();
                    $('#waste_water_floride_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_floride_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_floride_treatment == "") {
                    $('#waste_water_floride_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_floride_treatmentErrorMsg').show();
                    $('#waste_water_floride_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_floride_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_floride_name_location == "") {
                    $('#waste_water_floride_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_floride_name_locationErrorMsg').show();
                    $('#waste_water_floride_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_floride_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phosphate_source == "") {
                    $('#waste_water_phosphate_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_phosphate_sourceErrorMsg').show();
                    $('#waste_water_phosphate_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phosphate_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phosphate_discharge == "") {
                    $('#waste_water_phosphate_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_phosphate_dischargeErrorMsg').show();
                    $('#waste_water_phosphate_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phosphate_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phosphate_treatment == "") {
                    $('#waste_water_phosphate_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_phosphate_treatmentErrorMsg').show();
                    $('#waste_water_phosphate_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phosphate_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phosphate_name_location == "") {
                    $('#waste_water_phosphate_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_phosphate_name_locationErrorMsg').show();
                    $('#waste_water_phosphate_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phosphate_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nitrate_source == "") {
                    $('#waste_water_nitrate_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nitrate_sourceErrorMsg').show();
                    $('#waste_water_nitrate_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nitrate_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nitrate_discharge == "") {
                    $('#waste_water_nitrate_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nitrate_dischargeErrorMsg').show();
                    $('#waste_water_nitrate_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nitrate_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nitrate_treatment == "") {
                    $('#waste_water_nitrate_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nitrate_treatmentErrorMsg').show();
                    $('#waste_water_nitrate_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nitrate_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nitrate_name_location == "") {
                    $('#waste_water_nitrate_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nitrate_name_locationErrorMsg').show();
                    $('#waste_water_nitrate_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nitrate_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_iron_source == "") {
                    $('#waste_water_iron_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_iron_sourceErrorMsg').show();
                    $('#waste_water_iron_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_iron_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_iron_discharge == "") {
                    $('#waste_water_iron_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_iron_dischargeErrorMsg').show();
                    $('#waste_water_iron_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_iron_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_iron_treatment == "") {
                    $('#waste_water_iron_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_iron_treatmentErrorMsg').show();
                    $('#waste_water_iron_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_iron_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_iron_name_location == "") {
                    $('#waste_water_iron_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_iron_name_locationErrorMsg').show();
                    $('#waste_water_iron_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_iron_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_lead_source == "") {
                    $('#waste_water_lead_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_lead_sourceErrorMsg').show();
                    $('#waste_water_lead_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_lead_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_lead_discharge == "") {
                    $('#waste_water_lead_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_lead_dischargeErrorMsg').show();
                    $('#waste_water_lead_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_lead_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_lead_treatment == "") {
                    $('#waste_water_lead_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_lead_treatmentErrorMsg').show();
                    $('#waste_water_lead_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_lead_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_lead_name_location == "") {
                    $('#waste_water_lead_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_lead_name_locationErrorMsg').show();
                    $('#waste_water_lead_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_lead_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_manganese_source == "") {
                    $('#waste_water_manganese_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_manganese_sourceErrorMsg').show();
                    $('#waste_water_manganese_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_manganese_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_manganese_discharge == "") {
                    $('#waste_water_manganese_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_manganese_dischargeErrorMsg').show();
                    $('#waste_water_manganese_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_manganese_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_manganese_treatment == "") {
                    $('#waste_water_manganese_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_manganese_treatmentErrorMsg').show();
                    $('#waste_water_manganese_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_manganese_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_manganese_name_location == "") {
                    $('#waste_water_manganese_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_manganese_name_locationErrorMsg').show();
                    $('#waste_water_manganese_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_manganese_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_mercury_source == "") {
                    $('#waste_water_mercury_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_mercury_sourceErrorMsg').show();
                    $('#waste_water_mercury_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_mercury_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_mercury_discharge == "") {
                    $('#waste_water_mercury_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_mercury_dischargeErrorMsg').show();
                    $('#waste_water_mercury_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_mercury_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_mercury_treatment == "") {
                    $('#waste_water_mercury_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_mercury_treatmentErrorMsg').show();
                    $('#waste_water_mercury_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_mercury_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_mercury_name_location == "") {
                    $('#waste_water_mercury_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_mercury_name_locationErrorMsg').show();
                    $('#waste_water_mercury_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_mercury_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nickel_source == "") {
                    $('#waste_water_nickel_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nickel_sourceErrorMsg').show();
                    $('#waste_water_nickel_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nickel_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nickel_discharge == "") {
                    $('#waste_water_nickel_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nickel_dischargeErrorMsg').show();
                    $('#waste_water_nickel_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nickel_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nickel_treatment == "") {
                    $('#waste_water_nickel_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nickel_treatmentErrorMsg').show();
                    $('#waste_water_nickel_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nickel_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_nickel_name_location == "") {
                    $('#waste_water_nickel_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_nickel_name_locationErrorMsg').show();
                    $('#waste_water_nickel_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_nickel_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_oil_source == "") {
                    $('#waste_water_oil_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_oil_sourceErrorMsg').show();
                    $('#waste_water_oil_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_oil_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_oil_discharge == "") {
                    $('#waste_water_oil_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_oil_dischargeErrorMsg').show();
                    $('#waste_water_oil_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_oil_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_oil_treatment == "") {
                    $('#waste_water_oil_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_oil_treatmentErrorMsg').show();
                    $('#waste_water_oil_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_oil_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_oil_name_location == "") {
                    $('#waste_water_oil_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_oil_name_locationErrorMsg').show();
                    $('#waste_water_oil_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_oil_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ph_source == "") {
                    $('#waste_water_ph_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ph_sourceErrorMsg').show();
                    $('#waste_water_ph_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ph_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ph_discharge == "") {
                    $('#waste_water_ph_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ph_dischargeErrorMsg').show();
                    $('#waste_water_ph_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ph_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ph_treatment == "") {
                    $('#waste_water_ph_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ph_treatmentErrorMsg').show();
                    $('#waste_water_ph_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ph_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ph_name_location == "") {
                    $('#waste_water_ph_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ph_name_locationErrorMsg').show();
                    $('#waste_water_ph_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ph_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phenolic_source == "") {
                    $('#waste_water_phenolic_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_phenolic_sourceErrorMsg').show();
                    $('#waste_water_phenolic_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phenolic_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phenolic_discharge == "") {
                    $('#waste_water_phenolic_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_phenolic_dischargeErrorMsg').show();
                    $('#waste_water_phenolic_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phenolic_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phenolic_treatment == "") {
                    $('#waste_water_phenolic_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_phenolic_treatmentErrorMsg').show();
                    $('#waste_water_phenolic_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phenolic_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_phenolic_name_location == "") {
                    $('#waste_water_phenolic_name_location').html("Enter Voltage level in kV.");
                    $('#waste_water_phenolic_name_location').show();
                    $('#waste_water_phenolic_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_phenolic_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_selenium_source == "") {
                    $('#waste_water_selenium_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_selenium_sourceErrorMsg').show();
                    $('#waste_water_selenium_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_selenium_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_selenium_discharge == "") {
                    $('#waste_water_selenium_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_selenium_dischargeErrorMsg').show();
                    $('#waste_water_selenium_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_selenium_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_selenium_treatment == "") {
                    $('#waste_water_selenium_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_selenium_treatmentErrorMsg').show();
                    $('#waste_water_selenium_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_selenium_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_selenium_name_location == "") {
                    $('#waste_water_selenium_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_selenium_name_locationErrorMsg').show();
                    $('#waste_water_selenium_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_selenium_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_so4_source == "") {
                    $('#waste_water_so4_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_so4_sourceErrorMsg').show();
                    $('#waste_water_so4_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_so4_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_so4_discharge == "") {
                    $('#waste_water_so4_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_so4_dischargeErrorMsg').show();
                    $('#waste_water_so4_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_so4_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_so4_treatment == "") {
                    $('#waste_water_so4_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_so4_treatmentErrorMsg').show();
                    $('#waste_water_so4_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_so4_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_so4_name_location == "") {
                    $('#waste_water_so4_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_so4_name_locationErrorMsg').show();
                    $('#waste_water_so4_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_so4_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_s_source == "") {
                    $('#waste_water_s_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_s_sourceErrorMsg').show();
                    $('#waste_water_s_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_s_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_s_discharge == "") {
                    $('#waste_water_s_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_s_dischargeErrorMsg').show();
                    $('#waste_water_s_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_s_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_s_treatment == "") {
                    $('#waste_water_s_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_s_treatmentErrorMsg').show();
                    $('#waste_water_s_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_s_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_s_name_location == "") {
                    $('#waste_water_s_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_s_name_locationErrorMsg').show();
                    $('#waste_water_s_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_s_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tds_source == "") {
                    $('#waste_water_tds_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tds_sourceErrorMsg').show();
                    $('#waste_water_tds_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tds_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tds_discharge == "") {
                    $('#waste_water_tds_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tds_dischargeErrorMsg').show();
                    $('#waste_water_tds_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tds_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tds_treatment == "") {
                    $('#waste_water_tds_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tds_treatmentErrorMsg').show();
                    $('#waste_water_tds_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tds_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tds_name_location == "") {
                    $('#waste_water_tds_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tds_name_locationErrorMsg').show();
                    $('#waste_water_tds_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tds_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tss_source == "") {
                    $('#waste_water_tss_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tss_sourceErrorMsg').show();
                    $('#waste_water_tss_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tss_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tss_discharge == "") {
                    $('#waste_water_tss_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tss_dischargeErrorMsg').show();
                    $('#waste_water_tss_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tss_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tss_treatment == "") {
                    $('#waste_water_tss_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tss_treatmentErrorMsg').show();
                    $('#waste_water_tss_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tss_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tss_name_location == "") {
                    $('#waste_water_tss_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tss_name_locationErrorMsg').show();
                    $('#waste_water_tss_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tss_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_temp_source == "") {
                    $('#waste_water_temp_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_temp_sourceErrorMsg').show();
                    $('#waste_water_temp_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_temp_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_temp_discharge == "") {
                    $('#waste_water_temp_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_temp_dischargeErrorMsg').show();
                    $('#waste_water_temp_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_temp_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_temp_treatment == "") {
                    $('#waste_water_temp_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_temp_treatmentErrorMsg').show();
                    $('#waste_water_temp_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_temp_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_temp_name_location == "") {
                    $('#waste_water_temp_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_temp_name_locationErrorMsg').show();
                    $('#waste_water_temp_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_temp_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tkn_source == "") {
                    $('#waste_water_tkn_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tkn_sourceErrorMsg').show();
                    $('#waste_water_tkn_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tkn_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tkn_discharge == "") {
                    $('#waste_water_tkn_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tkn_dischargeErrorMsg').show();
                    $('#waste_water_tkn_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tkn_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tkn_treatment == "") {
                    $('#waste_water_tkn_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tkn_treatmentErrorMsg').show();
                    $('#waste_water_tkn_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tkn_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_tkn_name_location == "") {
                    $('#waste_water_tkn_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_tkn_name_locationErrorMsg').show();
                    $('#waste_water_tkn_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_tkn_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_residual_cloride_source == "") {
                    $('#waste_water_residual_cloride_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_residual_cloride_sourceErrorMsg').show();
                    $('#waste_water_residual_cloride_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_residual_cloride_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_residual_cloride_discharge == "") {
                    $('#waste_water_residual_cloride_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_residual_cloride_dischargeErrorMsg').show();
                    $('#waste_water_residual_cloride_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_residual_cloride_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_residual_cloride_treatment == "") {
                    $('#waste_water_residual_cloride_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_residual_cloride_treatmentErrorMsg').show();
                    $('#waste_water_residual_cloride_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_residual_cloride_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_residual_cloride_name_location == "") {
                    $('#waste_water_residual_cloride_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_residual_cloride_name_locationErrorMsg').show();
                    $('#waste_water_residual_cloride_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_residual_cloride_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_zinc_source == "") {
                    $('#waste_water_zinc_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_zinc_sourceErrorMsg').show();
                    $('#waste_water_zinc_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_zinc_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_zinc_discharge == "") {
                    $('#waste_water_zinc_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_zinc_dischargeErrorMsg').show();
                    $('#waste_water_zinc_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_zinc_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_zinc_treatment == "") {
                    $('#waste_water_zinc_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_zinc_treatmentErrorMsg').show();
                    $('#waste_water_zinc_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_zinc_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_zinc_name_location == "") {
                    $('#waste_water_zinc_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_zinc_name_locationErrorMsg').show();
                    $('#waste_water_zinc_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_zinc_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ammonia_source == "") {
                    $('#waste_water_ammonia_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ammonia_sourceErrorMsg').show();
                    $('#waste_water_ammonia_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ammonia_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ammonia_discharge == "") {
                    $('#waste_water_ammonia_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ammonia_dischargeErrorMsg').show();
                    $('#waste_water_ammonia_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ammonia_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ammonia_treatment == "") {
                    $('#waste_water_ammonia_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ammonia_treatmentErrorMsg').show();
                    $('#waste_water_ammonia_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ammonia_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_ammonia_name_location == "") {
                    $('#waste_water_ammonia_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_ammonia_name_locationErrorMsg').show();
                    $('#waste_water_ammonia_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_ammonia_name_location').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_colour_source == "") {
                    $('#waste_water_colour_sourceErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_colour_sourceErrorMsg').show();
                    $('#waste_water_colour_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_colour_source').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_colour_discharge == "") {
                    $('#waste_water_colour_dischargeErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_colour_dischargeErrorMsg').show();
                    $('#waste_water_colour_dischargeErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_colour_discharge').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_colour_treatment == "") {
                    $('#waste_water_colour_treatmentErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_colour_treatmentErrorMsg').show();
                    $('#waste_water_colour_treatmentErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_colour_treatment').focus();
                }
                else if (en_waste_water_generate_value == 'Yes' && waste_water_colour_name_location == "") {
                    $('#waste_water_colour_name_locationErrorMsg').html("Enter Voltage level in kV.");
                    $('#waste_water_colour_name_locationErrorMsg').show();
                    $('#waste_water_colour_name_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#waste_water_colour_name_location').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_effluent_details/",
                            data: $('#effluent_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#effluent_successMsg').html("Saved Successfully");
                                    $('#effluent_successMsg').show();
                                    $('#effluent_successMsg').focus();
                                    setTimeout(function () {
                                        $('#effluent_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#headingElevenBtn").removeAttr("disabled");
                                        $("#collapseEleven").addClass("show");
                                        $("#collapseNine").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;

                                    $('#effluent_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#effluent_errorMsg').show();
                                    $('#effluent_errorMsg').focus();
                                    setTimeout(function () {
                                        $('#effluent_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }

            function save_industry_emission_details() {
                let en_industry_emission_generate = $("input[name=en_industry_emission_generate]:checked").length;
                let en_industry_emission_generate_value = $("input[name=en_industry_emission_generate]:checked").val();
                let en_spm_emission_expected = $('#en_spm_emission_expected').val();
                let en_so2_emission_expected = $('#en_so2_emission_expected').val();
                let en_nox_emission_expected = $('#en_nox_emission_expected').val();
                let en_co_emission_expected = $('#en_co_emission_expected').val();
                let en_fluoride_emission_expected = $('#en_fluoride_emission_expected').val();
                let en_air_pollution_control_device_capacity = $('#en_air_pollution_control_device_capacity').val();
                let en_air_pollution_control_pcd_dimension = $('#en_air_pollution_control_pcd_dimension').val();

                if (en_industry_emission_generate < 1) {
                    $('#en_industry_emission_generateErrorMsg').html("Please Select One.");
                    $('#en_industry_emission_generateErrorMsg').show();
                    $('#en_industry_emission_generateErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_industry_emission_generate').focus();
                }
                else if (en_industry_emission_generate_value == 'Yes' && en_so2_emission_expected == "") {
                    $('#en_spm_emission_expectedErrorMsg').html("Enter SPM.");
                    $('#en_spm_emission_expectedErrorMsg').show();
                    $('#en_spm_emission_expectedErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_spm_emission_expected').focus();
                }
                else if (en_industry_emission_generate_value == 'Yes' && en_spm_emission_expected == "") {
                    $('#en_spm_emission_expectedErrorMsg').html("Enter SO2.");
                    $('#en_spm_emission_expectedErrorMsg').show();
                    $('#en_spm_emission_expectedErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_spm_emission_expected').focus();
                }
                else if (en_industry_emission_generate_value == 'Yes' && en_nox_emission_expected == "") {
                    $('#en_nox_emission_expectedErrorMsg').html("Enter NOx.");
                    $('#en_nox_emission_expectedErrorMsg').show();
                    $('#en_nox_emission_expectedErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_nox_emission_expected').focus();
                }
                else if (en_industry_emission_generate_value == 'Yes' && en_co_emission_expected == "") {
                    $('#en_co_emission_expectedErrorMsg').html("Enter CO.");
                    $('#en_co_emission_expectedErrorMsg').show();
                    $('#en_co_emission_expectedErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_co_emission_expected').focus();
                }
                else if (en_industry_emission_generate_value == 'Yes' && en_fluoride_emission_expected == "") {
                    $('#en_fluoride_emission_expectedErrorMsg').html("Enter Total Fluoride.");
                    $('#en_fluoride_emission_expectedErrorMsg').show();
                    $('#en_fluoride_emission_expectedErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_fluoride_emission_expected').focus();
                }
                else if (en_air_pollution_control_device_capacity == "") {
                    $('#en_air_pollution_control_device_capacityErrorMsg').html("Enter Capacity.");
                    $('#en_air_pollution_control_device_capacityErrorMsg').show();
                    $('#en_air_pollution_control_device_capacityErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_air_pollution_control_device_capacity').focus();
                }
                else if (en_air_pollution_control_pcd_dimension == "") {
                    $('#en_air_pollution_control_pcd_dimensionErrorMsg').html("Enter Components and dimensions of the PCD.");
                    $('#en_air_pollution_control_pcd_dimensionErrorMsg').show();
                    $('#en_air_pollution_control_pcd_dimensionErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_air_pollution_control_pcd_dimension').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_industry_emission_details/",
                            data: $('#industry_emission_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#industry_emission_successMsg').html("Saved Successfully");
                                    $('#industry_emission_successMsg').show();
                                    $('#industry_emission_successMsg').focus();
                                    setTimeout(function () {
                                        $('#industry_emission_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#headingTwelveBtn").removeAttr("disabled");
                                        $("#collapseTwelve").addClass("show");
                                        $("#collapseEleven").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;

                                    $('#industry_emission_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#industry_emission_errorMsg').show();
                                    $('#industry_emission_errorMsg').focus();
                                    setTimeout(function () {
                                        $('#industry_emission_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }


            function check_wastewater(value) {
                if (value == 'Yes') {
                    $('.effulent_details').show();
                }
                else {
                    $('.effulent_details').hide();
                }
            }

            function check_industry_emission(value) {
                if (value == 'Yes') {
                    $('.industry_details').show();
                }
                else {
                    $('.industry_details').hide();
                }
            }

            function save_energy_project_details() {
                let project_objective = $('#project_objective').val();
                let no_of_workers = $('#no_of_workers').val();
                let project_output = $('#project_output').val();
                let project_cost = $('#project_cost').val();
                let project_duration = $('#project_duration').val();
                let proposed_route_reason = $('#proposed_route_reason').val();
                let power_generation = $('#power_generation').val();
                let water_excavated_muck = $("input[name=water_excavated_muck]:checked").length


                if (project_objective == "") {
                    $('#project_objectiveErrorMsg').html("Enter Project Objective");
                    $('#project_objectiveErrorMsg').show();
                    $('#project_objectiveErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_objective').focus();
                }
                else if (no_of_workers == "") {
                    $('#no_of_workersErrorMsg').html("Enter No Of Workers");
                    $('#no_of_workersErrorMsg').show();
                    $('#no_of_workersErrorMsg').delay(2000).fadeOut('slow');
                    $('#no_of_workers').focus();
                }
                else if (project_output == "") {
                    $('#project_outputErrorMsg').html("Enter Project Output");
                    $('#project_outputErrorMsg').show();
                    $('#project_outputErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_output').focus();
                }
                else if (project_cost == "") {
                    $('#project_costErrorMsg').html("Enter Project Cost");
                    $('#project_costErrorMsg').show();
                    $('#project_costErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_cost').focus();
                }
                else if (project_duration == "") {
                    $('#project_durationErrorMsg').html("Enter Project Duration");
                    $('#project_durationErrorMsg').show();
                    $('#project_durationErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_duration').focus();
                }
                else if (power_generation == "") {
                    $('#power_generationErrorMsg').html("Enter Reason");
                    $('#power_generationErrorMsg').show();
                    $('#power_generationErrorMsg').delay(2000).fadeOut('slow');
                    $('#power_generation').focus();
                }
                else if (water_excavated_muck < 1) {
                    $('#water_excavated_muckErrorMsg').html("Please Choose One");
                    $('#water_excavated_muckErrorMsg').show();
                    $('#water_excavated_muckErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_excavated_muck').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_project_details/",
                            data: $('#project_details_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#project_details_successMsg').html("Saved Successfully");
                                    $('#project_details_successMsg').show();
                                    $('#project_details_successMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#collapseFourBtn").removeAttr("disabled");
                                        $("#collapseFour").addClass("show");
                                        $("#collapseProjectDetails").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;
                                    $('#project_details_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#project_details_errorMsg').show();
                                    $('#project_details_errorMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }

            function add_energy_raw_material_details() {
                let application_no = $('#application_no').val();
                let raw_material = $('#raw_material').val();
                let raw_material_qty = $('#raw_material_qty').val();
                let raw_material_source = $('#raw_material_source').val();
                let raw_material_storage_method = $('#raw_material_storage_method').val();

                if (raw_material == "") {
                    $('#raw_materialErrorMsg').html("Enter Raw Material");
                    $('#raw_materialErrorMsg').show();
                    $('#raw_materialErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material').focus();
                }
                else if (raw_material_qty == "") {
                    $('#raw_material_qtyErrorMsg').html("Enter Qty");
                    $('#raw_material_qtyErrorMsg').show();
                    $('#raw_material_qtyErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material_qty').focus();
                }
                else if (raw_material_source == "") {
                    $('#raw_material_sourceErrorMsg').html("Enter Source");
                    $('#raw_material_sourceErrorMsg').show();
                    $('#raw_material_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material_source').focus();
                }
                else if (raw_material_storage_method == "") {
                    $('#raw_material_storage_methodErrorMsg').html("Select Storage Method");
                    $('#raw_material_storage_methodErrorMsg').show();
                    $('#raw_material_storage_methodErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material_storage_method').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/add_raw_materials/",
                            data: { 'application_no': application_no, 'raw_material': raw_material, 'qty': raw_material_qty, 'source': raw_material_source, 'storage_method': raw_material_storage_method, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#raw_material_SuccessMsg').html("Add Successful");
                                $('#raw_material_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#raw_materials_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#raw_materials_div').html(responseText);
                                }, 2000);
                                $('#raw_materials_form')[0].reset();
                            }
                        });
                }
            }


            function raw_materials_details_edit(record_id, application_no, raw_material, qty, source, storage_method) {
                $('#edit_raw_material_record_id').val(record_id);
                $('#edit_raw_material_app_no').val(application_no);
                $('#edit_raw_material').val(raw_material);
                $('#edit_raw_material_qty').val(qty);
                $('#edit_raw_material_source').val(source);
                $('#edit_raw_material_storage_method').val(storage_method);
                $('#edit_raw_materials_modal').modal('show');
            }

            function update_energy_raw_material_details() {
                let record_id = $('#edit_raw_material_record_id').val();
                let application_no = $('#edit_raw_material_app_no').val();
                let raw_material = $('#edit_raw_material').val();
                let raw_material_qty = $('#edit_raw_material_qty').val();
                let raw_material_source = $('#edit_raw_material_source').val();
                let raw_material_storage_method = $('#edit_raw_material_storage_method').val();

                if (raw_material == "") {
                    $('#raw_materialErrorMsg').html("Enter Raw Material");
                    $('#raw_materialErrorMsg').show();
                    $('#raw_materialErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material').focus();
                }
                else if (raw_material_qty == "") {
                    $('#raw_material_qtyErrorMsg').html("Enter Qty");
                    $('#raw_material_qtyErrorMsg').show();
                    $('#raw_material_qtyErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material_qty').focus();
                }
                else if (raw_material_source == "") {
                    $('#raw_material_sourceErrorMsg').html("Enter Source");
                    $('#raw_material_sourceErrorMsg').show();
                    $('#raw_material_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material_source').focus();
                }
                else if (raw_material_storage_method == "") {
                    $('#raw_material_storage_methodErrorMsg').html("Select Storage Method");
                    $('#raw_material_storage_methodErrorMsg').show();
                    $('#raw_material_storage_methodErrorMsg').delay(2000).fadeOut('slow');
                    $('#raw_material_storage_method').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/update_raw_materials/",
                            data: { 'record_id': record_id, 'application_no': application_no, 'raw_material': raw_material, 'qty': raw_material_qty, 'source': raw_material_source, 'storage_method': raw_material_storage_method, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#edit_raw_material_SuccessMsg').html("Add Successful");
                                $('#edit_raw_material_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#edit_raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#edit_raw_materials_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#raw_materials_div').html(responseText);
                                }, 2000);
                            }
                        });
                }
            }

            function populate_delete_machine_equipment(record_id, application_no) {
                $('#delete_raw_material_record_id').val(record_id);
                $('#delete_raw_material_app_no').val(application_no);
                $('#delete_raw_material_modal').modal('show');
            }

            function delete_raw_material_details() {
                let record_id = $('#delete_raw_material_record_id').val();
                let application_no = $('#delete_raw_material_app_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_raw_materials/",
                        data: { 'record_id': record_id, 'application_no': application_no, csrfmiddlewaretoken: '{{ csrf_token }}' },
                        success: function (responseText) {
                            $('#delete_raw_material_SuccessMsg').html("Add Successful");
                            $('#delete_raw_material_SuccessMsg').show();
                            setTimeout(function () {
                                $('#delete_raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                            }, 2000);
                            setTimeout(function () {
                                $('#delete_raw_material_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#raw_materials_div').html(responseText);
                            }, 2000);
                        }
                    });
            }


            function add_energy_partner_details() {
                let application_no = $('#application_no').val();
                let partner_type = $('#partner_type').val();
                let partner_type_name = $('#partner_type_name').val();
                let partner_type_address = $('#partner_type_address').val();

                if (partner_type == "") {
                    $('#partner_typeErrorMsg').html("Enter Partner Type");
                    $('#partner_typeErrorMsg').show();
                    $('#partner_typeErrorMsg').delay(2000).fadeOut('slow');
                    $('#partner_type').focus();
                }
                else if (partner_type_name == "") {
                    $('#partner_type_nameErrorMsg').html("Enter Name");
                    $('#partner_type_nameErrorMsg').show();
                    $('#partner_type_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#partner_type_name').focus();
                }
                else if (partner_type_address == "") {
                    $('#partner_type_addressErrorMsg').html("Enter Address");
                    $('#partner_type_addressErrorMsg').show();
                    $('#partner_type_addressErrorMsg').delay(2000).fadeOut('slow');
                    $('#partner_type_address').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/add_product_details/",
                            data: { 'application_no': application_no, 'partner_type': partner_type, 'partner_type_name': partner_type_name, 'partner_type_address': partner_type_address, csrfmiddlewaretoken: '{{ csrf_token }}' },
                            success: function (responseText) {
                                $('#partner_type_SuccessMsg').html("Add Successful");
                                $('#partner_type_SuccessMsg').show();
                                setTimeout(function () {
                                    $('#partner_type_SuccessMsg').delay(2000).fadeOut('slow');
                                }, 2000);
                                setTimeout(function () {
                                    $('#partner_details_modal').modal('hide');
                                }, 2000);
                                setTimeout(function () {
                                    $('#partner_details_div').html(responseText);
                                }, 2000);
                                $('#partner_details_form')[0].reset();
                            }
                        });
                }
            }

            function populate_delete_partner_details(record_id, application_no) {
                $('#delete_partner_record_id').val(record_id);
                $('#delete_partner_app_no').val(application_no);
                $('#delete_partner_details_modal').modal('show');
            }

            function delete_partner_details() {
                let record_id = $('#delete_partner_details_record_id').val();
                let application_no = $('#delete_partner_details_app_no').val();

                $.ajax
                    ({
                        type: "POST",
                        url: "/delete_partner_details/",
                        data: { 'record_id': record_id, 'application_no': application_no, csrfmiddlewaretoken: '{{ csrf_token }}' },
                        success: function (responseText) {
                            $('#delete_raw_material_SuccessMsg').html("Add Successful");
                            $('#delete_raw_material_SuccessMsg').show();
                            setTimeout(function () {
                                $('#delete_raw_material_SuccessMsg').delay(2000).fadeOut('slow');
                            }, 2000);
                            setTimeout(function () {
                                $('#delete_raw_material_modal').modal('hide');
                            }, 2000);
                            setTimeout(function () {
                                $('#raw_materials_div').html(responseText);
                            }, 2000);
                        }
                    });
            }


            function check_ancillary_others(value) {
                if (value == 'Yes') {
                    $('.anc_others').show();
                }
                else {
                    $('.anc_others').hide();

                }
            }

            function save_solid_waste_details() {
                let en_impact_allocated_budget = $('#en_impact_allocated_budget').val();
                let en_impact_hazardous_waste_list = $('#en_impact_hazardous_waste_list').val();
                let en_impact_hazardous_waste_source = $('#en_impact_hazardous_waste_source').val();
                let en_impact_hazardous_waste_qty_annum = $('#en_impact_hazardous_waste_qty_annum').val();
                let en_impact_hazardous_waste_mgt_plan = $('#en_impact_hazardous_waste_mgt_plan').val();
                let en_impact_non_hazardous_waste_list = $('#en_impact_non_hazardous_waste_list').val();
                let en_impact_non_hazardous_waste_source = $('#en_impact_non_hazardous_waste_source').val();
                let en_impact_non_hazardous_waste_qty_annum = $('#en_impact_non_hazardous_waste_qty_annum').val();
                let en_impact_non_hazardous_waste_mgt_plan = $('#en_impact_non_hazardous_waste_mgt_plan').val();
                let en_impact_medical_waste_list = $('#en_impact_medical_waste_list').val();
                let en_impact_medical_waste_source = $('#en_impact_medical_waste_source').val();
                let en_impact_medical_waste_qty_annum = $('#en_impact_medical_waste_qty_annum').val();
                let en_impact_medical_waste_mgt_plan = $('#en_impact_medical_waste_mgt_plan').val();
                let en_impact_ewaste_list = $('#en_impact_ewaste_list').val();
                let en_impact_ewaste_source = $('#en_impact_ewaste_source').val();
                let en_impact_ewaste_qty_annum = $('#en_impact_ewaste_qty_annum').val();
                let en_impact_ewaste_mgt_plan = $('#en_impact_ewaste_mgt_plan').val();
                let en_impact_others_waste_list = $('#en_impact_others_waste_list').val();
                let en_impact_others_waste_source = $('#en_impact_others_waste_source').val();
                let en_impact_others_waste_qty_annum = $('#en_impact_others_waste_qty_annum').val();
                let en_impact_others_waste_mgt_plan = $('#en_impact_others_waste_mgt_plan').val();

                if (en_impact_allocated_budget == "") {
                    $('#en_impact_allocated_budgetErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_allocated_budgetErrorMsg').show();
                    $('#en_impact_allocated_budgetErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_allocated_budget').focus();
                }
                else if (en_impact_hazardous_waste_list == "") {
                    $('#en_impact_hazardous_waste_listErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_hazardous_waste_listErrorMsg').show();
                    $('#en_impact_hazardous_waste_listErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_hazardous_waste_list').focus();
                }
                else if (en_impact_hazardous_waste_source == "") {
                    $('#en_impact_hazardous_waste_sourceErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_hazardous_waste_sourceErrorMsg').show();
                    $('#en_impact_hazardous_waste_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_hazardous_waste_source').focus();
                }
                else if (en_impact_hazardous_waste_qty_annum == "") {
                    $('#en_impact_hazardous_waste_qty_annumErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_hazardous_waste_qty_annumErrorMsg').show();
                    $('#en_impact_hazardous_waste_qty_annumErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_hazardous_waste_qty_annum').focus();
                }
                else if (en_impact_hazardous_waste_mgt_plan == "") {
                    $('#en_impact_hazardous_waste_mgt_planErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_hazardous_waste_mgt_planErrorMsg').show();
                    $('#en_impact_hazardous_waste_mgt_planErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_hazardous_waste_mgt_plan').focus();
                }
                else if (en_impact_non_hazardous_waste_list == "") {
                    $('#en_impact_non_hazardous_waste_listErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_non_hazardous_waste_listErrorMsg').show();
                    $('#en_impact_non_hazardous_waste_listErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_non_hazardous_waste_list').focus();
                }
                else if (en_impact_non_hazardous_waste_source == "") {
                    $('#en_impact_non_hazardous_waste_sourceErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_non_hazardous_waste_sourceErrorMsg').show();
                    $('#en_impact_non_hazardous_waste_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_non_hazardous_waste_source').focus();
                }
                else if (en_impact_non_hazardous_waste_qty_annum == "") {
                    $('#en_impact_non_hazardous_waste_qty_annumErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_non_hazardous_waste_qty_annumErrorMsg').show();
                    $('#en_impact_non_hazardous_waste_qty_annumErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_non_hazardous_waste_qty_annum').focus();
                }
                else if (en_impact_non_hazardous_waste_mgt_plan == "") {
                    $('#en_impact_non_hazardous_waste_mgt_planErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_non_hazardous_waste_mgt_planErrorMsg').show();
                    $('#en_impact_non_hazardous_waste_mgt_planErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_non_hazardous_waste_mgt_plan').focus();
                }
                else if (en_impact_medical_waste_list == "") {
                    $('#en_impact_medical_waste_listErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_medical_waste_listErrorMsg').show();
                    $('#en_impact_medical_waste_listErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_medical_waste_list').focus();
                }
                else if (en_impact_medical_waste_source == "") {
                    $('#en_impact_medical_waste_sourceErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_medical_waste_sourceErrorMsg').show();
                    $('#en_impact_medical_waste_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_medical_waste_source').focus();
                }
                else if (en_impact_medical_waste_qty_annum == "") {
                    $('#en_impact_medical_waste_qty_annumErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_medical_waste_qty_annumErrorMsg').show();
                    $('#en_impact_medical_waste_qty_annumErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_medical_waste_qty_annum').focus();
                }
                else if (en_impact_medical_waste_mgt_plan == "") {
                    $('#en_impact_medical_waste_mgt_planErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_medical_waste_mgt_planErrorMsg').show();
                    $('#en_impact_medical_waste_mgt_planErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_medical_waste_mgt_plan').focus();
                }
                else if (en_impact_ewaste_list == "") {
                    $('#en_impact_ewaste_listErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_ewaste_listErrorMsg').show();
                    $('#en_impact_ewaste_listErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_ewaste_list').focus();
                }
                else if (en_impact_ewaste_source == "") {
                    $('#en_impact_ewaste_sourceErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_ewaste_sourceErrorMsg').show();
                    $('#en_impact_ewaste_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_ewaste_source').focus();
                }
                else if (en_impact_ewaste_qty_annum == "") {
                    $('#en_impact_ewaste_qty_annumErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_ewaste_qty_annumErrorMsg').show();
                    $('#en_impact_ewaste_qty_annumErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_ewaste_qty_annum').focus();
                }
                else if (en_impact_ewaste_mgt_plan == "") {
                    $('#en_impact_ewaste_mgt_planErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_ewaste_mgt_planErrorMsg').show();
                    $('#en_impact_ewaste_mgt_planErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_ewaste_mgt_plan').focus();
                }
                else if (en_impact_others_waste_list == "") {
                    $('#en_impact_others_waste_listErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_others_waste_listErrorMsg').show();
                    $('#en_impact_others_waste_listErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_others_waste_list').focus();
                }
                else if (en_impact_others_waste_source == "") {
                    $('#en_impact_others_waste_sourceErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_others_waste_sourceErrorMsg').show();
                    $('#en_impact_others_waste_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_others_waste_source').focus();
                }
                else if (en_impact_others_waste_qty_annum == "") {
                    $('#en_impact_others_waste_qty_annumErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_others_waste_qty_annumErrorMsg').show();
                    $('#en_impact_others_waste_qty_annumErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_others_waste_qty_annum').focus();
                }
                else if (en_impact_others_waste_mgt_plan == "") {
                    $('#en_impact_others_waste_mgt_planErrorMsg').html("Provide an allocated budget for the management plan proposed.");
                    $('#en_impact_others_waste_mgt_planErrorMsg').show();
                    $('#en_impact_others_waste_mgt_planErrorMsg').delay(2000).fadeOut('slow');
                    $('#en_impact_others_waste_mgt_plan').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_solid_waste_details/",
                            data: $('#solid_waste_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#solid_waste_successMsg').html("Saved Successfully");
                                    $('#solid_waste_successMsg').show();
                                    $('#solid_waste_successMsg').focus();
                                    setTimeout(function () {
                                        $('#solid_waste_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#headingTwelveBtn").removeAttr("disabled");
                                        $("#collapseTwelve").addClass("show");
                                        $("#collapseEight").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;
                                    $('#solid_waste_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#solid_waste_errorMsg').show();
                                    $('#solid_waste_errorMsg').focus();
                                    setTimeout(function () {
                                        $('#solid_waste_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }


            function save_road_application() {
                let project_name = $('#project_name').val();
                let dzongkhag_throm = $("input[name=dzongkhag_throm]:checked").length;
                let dzongkhag_throm_val = $("input[name=dzongkhag_throm]:checked").val();
                let thromde_id = $('#thromde_id').val();
                let dzongkhag_code = $('#dzongkhag').val();
                let gewog_code = $('#gewog').val();
                let village_code = $('#vil_chiwog').val();
                let bl_protected_area_name = $('#bl_protected_area_name').val();
                let bl_protected_area_distance = $('#bl_protected_area_distance').val();
                let bl_migratory_route_name = $('#bl_migratory_route_name').val();
                let bl_migratory_route_distance = $('#bl_migratory_route_distance').val();
                let bl_wetland_name = $('#bl_wetland_name').val();
                let bl_wetland_distance = $('#bl_wetland_distance').val();
                let bl_water_bodies_name = $('#bl_water_bodies_name').val();
                let bl_water_bodies_distance = $('#bl_water_bodies_distance').val();
                let bl_fmu_name = $('#bl_fmu_name').val();
                let bl_fmu_distance = $('#bl_fmu_distance').val();
                let bl_agricultural_name = $('#bl_agricultural_name').val();
                let bl_agricultural_distance = $('#bl_agricultural_distance').val();
                let bl_settlement_name = $('#bl_settlement_name').val();
                let bl_settlement_distance = $('#bl_settlement_distance').val();
                let bl_road_name = $('#bl_road_name').val();
                let bl_road_distance = $('#bl_road_distance').val();
                let bl_public_infra_name = $('#bl_public_infra_name').val();
                let bl_public_infra_distance = $('#bl_public_infra_distance').val();
                let bl_school_name = $('#bl_school_name').val();
                let bl_school_distance = $('#bl_school_distance').val();
                let bl_heritage_name = $('#bl_heritage_name').val();
                let bl_heritage_distance = $('#bl_heritage_distance').val();
                let bl_tourist_facility_name = $('#bl_tourist_facility_name').val();
                let bl_tourist_facility_distance = $('#bl_tourist_facility_distance').val();
                let bl_impt_installation_name = $('#bl_impt_installation_name').val();
                let bl_impt_installation_distance = $('#bl_impt_installation_distance').val();
                let bl_industries_name = $('#bl_industries_name').val();
                let bl_industries_distance = $('#bl_industries_distance').val();
                let bl_others = $('#bl_others').val();
                let bl_others_name = $('#bl_others_name').val();
                let bl_others_distance = $('#bl_others_distance').val();

                if (project_name == "") {
                    $('#project_nameErrorMsg').html("Enter Name of Project");
                    $('#project_nameErrorMsg').show();
                    $('#project_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_name').focus();
                }
                else if (dzongkhag_throm == "") {
                    $('#dzongkhag_thromErrorMsg').html("Choose One");
                    $('#dzongkhag_thromErrorMsg').show();
                    $('#dzongkhag_thromErrorMsg').delay(2000).fadeOut('slow');
                    $('#dzongkhag_throm').focus();
                }
                else if (dzongkhag_throm_val == "Thromde" && thromde_id == "") {
                    $('#thromde_idErrorMsg').html("Select Dzongkhag");
                    $('#thromde_idErrorMsg').show();
                    $('#thromde_idErrorMsg').delay(2000).fadeOut('slow');
                    $('#thromde_id').focus();
                }
                else if (dzongkhag_throm_val == "Dzongkhag" && dzongkhag_code == "") {
                    $('#dzongkhagErrorMsg').html("Select Dzongkhag");
                    $('#dzongkhagErrorMsg').show();
                    $('#dzongkhagErrorMsg').delay(2000).fadeOut('slow');
                    $('#dzongkhag').focus();
                }
                else if (dzongkhag_throm_val == "Dzongkhag" && gewog_code == "") {
                    $('#gewogErrorMsg').html("Select Gewog");
                    $('#gewogErrorMsg').show();
                    $('#gewogErrorMsg').delay(2000).fadeOut('slow');
                    $('#gewog').focus();
                }
                else if (dzongkhag_throm_val == "Dzongkhag" && village_code == "") {
                    $('#vil_chiwogErrorMsg').html("Select Village");
                    $('#vil_chiwogErrorMsg').show();
                    $('#vil_chiwogErrorMsg').delay(2000).fadeOut('slow');
                    $('#vil_chiwog').focus();
                }
                else if (bl_protected_area_name == "") {
                    $('#bl_protected_area_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_protected_area_nameErrorMsg').show();
                    $('#bl_protected_area_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_protected_area_name').focus();
                }
                else if (bl_protected_area_distance == "") {
                    $('#bl_protected_area_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_protected_area_distanceErrorMsg').show();
                    $('#bl_protected_area_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_protected_area_distance').focus();
                }
                else if (bl_migratory_route_name == "") {
                    $('#bl_migratory_route_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_migratory_route_nameErrorMsg').show();
                    $('#bl_migratory_route_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_migratory_route_name').focus();
                }
                else if (bl_migratory_route_distance == "") {
                    $('#bl_migratory_route_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_migratory_route_distanceErrorMsg').show();
                    $('#bl_migratory_route_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_migratory_route_distance').focus();
                }
                else if (bl_wetland_name == "") {
                    $('#bl_wetland_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_wetland_nameErrorMsg').show();
                    $('#bl_wetland_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_wetland_name').focus();
                }
                else if (bl_wetland_distance == "") {
                    $('#bl_wetland_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_wetland_distanceErrorMsg').show();
                    $('#bl_wetland_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_wetland_distance').focus();
                }
                else if (bl_water_bodies_name == "") {
                    $('#bl_water_bodies_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_water_bodies_nameErrorMsg').show();
                    $('#bl_water_bodies_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_water_bodies_name').focus();
                }
                else if (bl_water_bodies_distance == "") {
                    $('#bl_water_bodies_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_water_bodies_distanceErrorMsg').show();
                    $('#bl_water_bodies_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_water_bodies_distance').focus();
                }
                else if (bl_fmu_name == "") {
                    $('#bl_fmu_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_fmu_nameErrorMsg').show();
                    $('#bl_fmu_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_fmu_name').focus();
                }
                else if (bl_fmu_distance == "") {
                    $('#bl_fmu_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_fmu_distanceErrorMsg').show();
                    $('#bl_fmu_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_fmu_distance').focus();
                }
                else if (bl_agricultural_name == "") {
                    $('#bl_agricultural_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_agricultural_nameErrorMsg').show();
                    $('#bl_agricultural_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_agricultural_name').focus();
                }
                else if (bl_agricultural_distance == "") {
                    $('#bl_agricultural_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_agricultural_distanceErrorMsg').show();
                    $('#bl_agricultural_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_agricultural_distance').focus();
                }
                else if (bl_settlement_name == "") {
                    $('#bl_settlement_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_settlement_nameErrorMsg').show();
                    $('#bl_settlement_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_settlement_name').focus();
                }
                else if (bl_settlement_distance == "") {
                    $('#bl_settlement_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_settlement_distanceErrorMsg').show();
                    $('#bl_settlement_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_settlement_distance').focus();
                }
                else if (bl_road_name == "") {
                    $('#bl_road_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_road_nameErrorMsg').show();
                    $('#bl_road_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_road_name').focus();
                }
                else if (bl_road_distance == "") {
                    $('#bl_road_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_road_distanceErrorMsg').show();
                    $('#bl_road_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_road_distance').focus();
                }
                else if (bl_public_infra_name == "") {
                    $('#bl_public_infra_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_public_infra_nameErrorMsg').show();
                    $('#bl_public_infra_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_public_infra_name').focus();
                }
                else if (bl_public_infra_distance == "") {
                    $('#bl_public_infra_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_public_infra_distanceErrorMsg').show();
                    $('#bl_public_infra_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_public_infra_distance').focus();
                }
                else if (bl_school_name == "") {
                    $('#bl_school_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_school_nameErrorMsg').show();
                    $('#bl_school_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_school_name').focus();
                }
                else if (bl_school_distance == "") {
                    $('#bl_school_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_school_distanceErrorMsg').show();
                    $('#bl_school_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_school_distance').focus();
                }
                else if (bl_heritage_name == "") {
                    $('#bl_heritage_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_heritage_nameErrorMsg').show();
                    $('#bl_heritage_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_heritage_name').focus();
                }
                else if (bl_heritage_distance == "") {
                    $('#bl_heritage_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_heritage_distanceErrorMsg').show();
                    $('#bl_heritage_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_heritage_distance').focus();
                }
                else if (bl_tourist_facility_name == "") {
                    $('#bl_tourist_facility_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_tourist_facility_nameErrorMsg').show();
                    $('#bl_tourist_facility_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_tourist_facility_name').focus();
                }
                else if (bl_tourist_facility_distance == "") {
                    $('#bl_tourist_facility_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_tourist_facility_distanceErrorMsg').show();
                    $('#bl_tourist_facility_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_tourist_facility_distance').focus();
                }
                else if (bl_impt_installation_name == "") {
                    $('#bl_impt_installation_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_impt_installation_nameErrorMsg').show();
                    $('#bl_impt_installation_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_impt_installation_name').focus();
                }
                else if (bl_impt_installation_distance == "") {
                    $('#bl_impt_installation_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_impt_installation_distanceErrorMsg').show();
                    $('#bl_impt_installation_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_impt_installation_distance').focus();
                }
                else if (bl_industries_name == "") {
                    $('#bl_industries_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_industries_nameErrorMsg').show();
                    $('#bl_industries_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_industries_name').focus();
                }
                else if (bl_industries_distance == "") {
                    $('#bl_industries_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_industries_distanceErrorMsg').show();
                    $('#bl_industries_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_industries_distance').focus();
                }
                else if (bl_others == "") {
                    $('#bl_othersErrorMsg').html("Select Slope/Gradient");
                    $('#bl_othersErrorMsg').show();
                    $('#bl_othersErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_others').focus();
                }
                else if (bl_others_name == "") {
                    $('#bl_others_nameErrorMsg').html("Select Slope/Gradient");
                    $('#bl_others_nameErrorMsg').show();
                    $('#bl_others_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_others_name').focus();
                }
                else if (bl_others_distance == "") {
                    $('#bl_others_distanceErrorMsg').html("Select Slope/Gradient");
                    $('#bl_others_distanceErrorMsg').show();
                    $('#bl_others_distanceErrorMsg').delay(2000).fadeOut('slow');
                    $('#bl_others_distance').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/save_road_application/",
                            data: $('#road_application_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#application_form_successMsg').html("Saved Successfully");
                                    $('#application_form_successMsg').show();
                                    $('#application_form_successMsg').focus();
                                    setTimeout(function () {
                                        $('#application_form_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#ProjectDetailsBtn").removeAttr("disabled");
                                        $("#collapseProjectDetails").addClass("show");
                                        $("#collapseOne").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;

                                    $('#application_form_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#application_form_errorMsg').show();
                                    $('#application_form_errorMsg').focus();

                                    setTimeout(function () {
                                        $('#application_form_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }

            }


            function road_project_details() {
                let project_objective = $('#project_objective').val();
                let proposed_route_reason = $('#proposed_route_reason').val();
                let project_cost = $('#project_cost').val();
                let project_duration = $('#project_duration').val();
                let road_length = $('#road_length').val();
                let starting_point = $('#starting_point').val();
                let terminating_point = $('#terminating_point').val();
                let road_row_width = $('#road_row_width').val();
                let formation_width = $('#formation_width').val();
                let pavement_width = $('#pavement_width').val();
                let pavement_material = $('#pavement_material').val();
                let extracted_material_vol = $('#extracted_material_vol').val();
                let maximum_road_gradient = $('#maximum_road_gradient').val();
                let cross_drains = $('#cross_drains').val();
                let box_culvert = $('#box_culvert').val();
                let bridges = $('#bridges').val();
                let bridge_width = $('#bridge_width').val();
                let bridge_length = $('#bridge_length').val();
                let side_drain = $('#side_drain').val();
                let side_drain_length = $('#side_drain_length').val();
                let side_drain_dimensions = $('#side_drain_dimensions').val();
                let box_drain_length = $('#box_drain_length').val();

                if (project_objective == "") {
                    $('#project_objectiveErrorMsg').html("Enter Project Objective");
                    $('#project_objectiveErrorMsg').show();
                    $('#project_objectiveErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_objective').focus();
                }
                else if (proposed_route_reason == "") {
                    $('#proposed_route_reasonErrorMsg').html("Enter Reason for selecting proposed route");
                    $('#proposed_route_reasonErrorMsg').show();
                    $('#proposed_route_reasonErrorMsg').delay(2000).fadeOut('slow');
                    $('#proposed_route_reason').focus();
                }
                else if (project_cost == "") {
                    $('#project_costErrorMsg').html("Enter Project Cost");
                    $('#project_costErrorMsg').show();
                    $('#project_costErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_cost').focus();
                }
                else if (project_duration == "") {
                    $('#project_durationErrorMsg').html("Enter Project Duration");
                    $('#project_durationErrorMsg').show();
                    $('#project_durationErrorMsg').delay(2000).fadeOut('slow');
                    $('#project_duration').focus();
                }
                else if (road_length == "") {
                    $('#road_lengthErrorMsg').html("Please Length of Road.");
                    $('#road_lengthErrorMsg').show();
                    $('#road_lengthErrorMsg').delay(2000).fadeOut('slow');
                    $('#road_length').focus();
                }
                else if (starting_point == "") {
                    $('#starting_pointErrorMsg').html("Enter Starting Point.");
                    $('#starting_pointErrorMsg').show();
                    $('#starting_pointErrorMsg').delay(2000).fadeOut('slow');
                    $('#starting_point').focus();
                }
                else if (terminating_point == "") {
                    $('#terminating_pointErrorMsg').html("Enter Terminating Point.");
                    $('#terminating_pointErrorMsg').show();
                    $('#terminating_pointErrorMsg').delay(2000).fadeOut('slow');
                    $('#terminating_point').focus();
                }
                else if (road_row_width == "") {
                    $('#road_row_widthErrorMsg').html("Enter Road Row Width.");
                    $('#road_row_widthErrorMsg').show();
                    $('#road_row_widthErrorMsg').delay(2000).fadeOut('slow');
                    $('#road_row_width').focus();
                }
                else if (formation_width == "") {
                    $('#formation_widthErrorMsg').html("Enter Formation Width.");
                    $('#formation_widthErrorMsg').show();
                    $('#formation_widthErrorMsg').delay(2000).fadeOut('slow');
                    $('#formation_width').focus();
                }
                else if (pavement_width == "") {
                    $('#pavement_widthErrorMsg').html("Enter Pavement Width.");
                    $('#pavement_widthErrorMsg').show();
                    $('#pavement_widthErrorMsg').delay(2000).fadeOut('slow');
                    $('#pavement_width').focus();
                }
                else if (pavement_material == "") {
                    $('#pavement_materialErrorMsg').html("Enter Pavement material.");
                    $('#pavement_materialErrorMsg').show();
                    $('#pavement_materialErrorMsg').delay(2000).fadeOut('slow');
                    $('#pavement_material').focus();
                }
                else if (extracted_material_vol == "") {
                    $('#extracted_material_volErrorMsg').html("Enter Road Row Width.");
                    $('#extracted_material_volErrorMsg').show();
                    $('#extracted_material_volErrorMsg').delay(2000).fadeOut('slow');
                    $('#extracted_material_vol').focus();
                }
                else if (maximum_road_gradient == "") {
                    $('#maximum_road_gradientErrorMsg').html("Enter Maximum road gradient.");
                    $('#maximum_road_gradientErrorMsg').show();
                    $('#maximum_road_gradientErrorMsg').delay(2000).fadeOut('slow');
                    $('#maximum_road_gradient').focus();
                }
                else if (cross_drains == "") {
                    $('#cross_drainsErrorMsg').html("Enter Cross Drains.");
                    $('#cross_drainsErrorMsg').show();
                    $('#cross_drainsErrorMsg').delay(2000).fadeOut('slow');
                    $('#cross_drains').focus();
                }
                else if (box_culvert == "") {
                    $('#box_culvertErrorMsg').html("Enter Box culvert.");
                    $('#box_culvertErrorMsg').show();
                    $('#box_culvertErrorMsg').delay(2000).fadeOut('slow');
                    $('#box_culvert').focus();
                }
                else if (bridges == "") {
                    $('#bridgesErrorMsg').html("Enter Bridges.");
                    $('#bridgesErrorMsg').show();
                    $('#bridgesErrorMsg').delay(2000).fadeOut('slow');
                    $('#bridges').focus();
                }
                else if (bridge_width == "") {
                    $('#bridge_widthErrorMsg').html("Enter Width of the bridges.");
                    $('#bridge_widthErrorMsg').show();
                    $('#bridge_widthErrorMsg').delay(2000).fadeOut('slow');
                    $('#bridge_width').focus();
                }
                else if (bridge_length == "") {
                    $('#bridge_lengthErrorMsg').html("Enter Total length of the bridges.");
                    $('#bridge_lengthErrorMsg').show();
                    $('#bridge_lengthErrorMsg').delay(2000).fadeOut('slow');
                    $('#bridge_width').focus();
                }
                else if (side_drain == "") {
                    $('#side_drainErrorMsg').html("V-shaped side drains dimensions.");
                    $('#side_drainErrorMsg').show();
                    $('#side_drainErrorMsg').delay(2000).fadeOut('slow');
                    $('#side_drain').focus();
                }
                else if (side_drain_length == "") {
                    $('#side_drain_lengthErrorMsg').html("Enter Total length of V-shaped drains.");
                    $('#side_drain_lengthErrorMsg').show();
                    $('#side_drain_lengthErrorMsg').delay(2000).fadeOut('slow');
                    $('#side_drain_length').focus();
                }
                else if (side_drain_dimensions == "") {
                    $('#side_drain_dimensionsErrorMsg').html("Enter Box shaped dimension.");
                    $('#side_drain_dimensionsErrorMsg').show();
                    $('#side_drain_dimensionsErrorMsg').delay(2000).fadeOut('slow');
                    $('#side_drain_dimensions').focus();
                }
                else if (box_drain_length == "") {
                    $('#box_drain_lengthErrorMsg').html("Enter Total lenght of box drains.");
                    $('#box_drain_lengthErrorMsg').show();
                    $('#box_drain_lengthErrorMsg').delay(2000).fadeOut('slow');
                    $('#box_drain_length').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/road_project_details/",
                            data: $('#project_details_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#project_details_successMsg').html("Saved Successfully");
                                    $('#project_details_successMsg').show();
                                    $('#project_details_successMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#collapseFourBtn").removeAttr("disabled");
                                        $("#collapseFour").addClass("show");
                                        $("#collapseProjectDetails").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;

                                    $('#project_details_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#project_details_errorMsg').show();
                                    $('#project_details_errorMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }


            function save_project_details_one() {
                let blast_required = $("input[name=blast_required]:checked").length;
                let blast_required_value = $("input[name=blast_required]:checked").val();
                let blast_type = $('#blast_type').val();
                let blast_qty = $('#blast_qty').val();
                let blast_location = $('#blast_location').val();
                let blast_frequency_time = $('#blast_frequency_time').val();

                if (blast_required < 1) {
                    $('#blast_requiredErrorMsg').html("Please Select One.");
                    $('#blast_requiredErrorMsg').show();
                    $('#blast_requiredErrorMsg').delay(2000).fadeOut('slow');
                    $('#blast_required').focus();
                }
                else if (blast_required_value == 'Yes' && blast_type == "") {
                    $('#blast_typeErrorMsg').html("Mention tupe of blasting.");
                    $('#blast_typeErrorMsg').show();
                    $('#blast_typeErrorMsg').delay(2000).fadeOut('slow');
                    $('#blast_type').focus();
                }
                else if (blast_required_value == 'Yes' && blast_qty == "") {
                    $('#blast_qtyErrorMsg').html("Mention type and quantities of explosive used.");
                    $('#blast_qtyErrorMsg').show();
                    $('#blast_qtyErrorMsg').delay(2000).fadeOut('slow');
                    $('#blast_qty').focus();
                }
                else if (blast_required_value == 'Yes' && blast_location == "") {
                    $('#blast_locationErrorMsg').html("Mention location(s) where the blasting is required.");
                    $('#blast_locationErrorMsg').show();
                    $('#blast_locationErrorMsg').delay(2000).fadeOut('slow');
                    $('#blast_location').focus();
                }
                else if (blast_required_value == 'Yes' && blast_frequency_time == "") {
                    $('#blast_frequency_timeErrorMsg').html("Mention Frequency and timing of blasting per day.");
                    $('#blast_frequency_timeErrorMsg').show();
                    $('#blast_frequency_timeErrorMsg').delay(2000).fadeOut('slow');
                    $('#blast_frequency_time').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/road_project_details_one/",
                            data: $('#project_details_one_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#project_details_one_successMsg').html("Saved Successfully");
                                    $('#project_details_one_successMsg').show();
                                    $('#project_details_one_successMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_one_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#ProjectTwoBtn").removeAttr("disabled");
                                        $("#collapseProjectTwo").addClass("show");
                                        $("#collapseFour").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;

                                    $('#project_details_one_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#project_details_one_errorMsg').show();
                                    $('#project_details_one_errorMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_one_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }

            function save_project_details_two() {
                let water_excavated_muck = $("input[name=water_excavated_muck]:checked").length;
                let water_required = $("input[name=water_required]:checked").length;
                let water_required_value = $('#water_required').val();
                let water_provide_by_iestate = $('#water_provided_by').val();
                let water_raw_material_source = $('#water_raw_material_source').val();
                let water_raw_material_qty_day = $('#water_raw_material_qty_day').val();
                let water_raw_material_recycle_day = $('#water_raw_material_recycle_day').val();
                let water_cleaning_source = $('#water_cleaning_source').val();
                let water_cleaning_qty_day = $('#water_cleaning_qty_day').val();
                let water_cleaning_recycle_day = $('#water_cleaning_recycle_day').val();
                let water_process_source = $('#water_process_source').val();
                let water_process_qty_day = $('#water_process_qty_day').val();
                let water_process_recycle_day = $('#water_process_recycle_day').val();
                let water_domestic_source = $('#water_domestic_source').val();
                let water_domestic_qty_day = $('#water_domestic_qty_day').val();
                let water_domestic_recycle_day = $('#water_domestic_recycle_day').val();
                let water_dust_compression_source = $('#water_dust_compression_source').val();
                let water_dust_compression_qty_day = $('#water_dust_compression_qty_day').val();
                let water_dust_compression_recycle_day = $('#water_dust_compression_recycle_day').val();
                let water_others_name = $('#water_others_name').val();
                let water_others_source = $('#water_others_source').val();
                let water_others_qty_day = $('#water_others_qty_day').val();

                if (water_excavated_muck < 1) {
                    $('#water_excavated_muckErrorMsg').html("Please Select One.");
                    $('#water_excavated_muckErrorMsg').show();
                    $('#water_excavated_muckErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_excavated_muck').focus();
                }
                else if (water_required < 1) {
                    $('#water_requiredErrorMsg').html("Please Select One.");
                    $('#water_requiredErrorMsg').show();
                    $('#water_requiredErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_required').focus();
                }
                else if (water_required_value == 'Yes' && water_raw_material_source == "") {
                    $('#water_raw_material_sourceErrorMsg').html("Please Select One.");
                    $('#water_raw_material_sourceErrorMsg').show();
                    $('#water_raw_material_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_raw_material_source').focus();
                }
                else if (water_required_value == 'Yes' && water_raw_material_qty_day == "") {
                    $('#water_raw_material_qty_dayErrorMsg').html("Please Select One.");
                    $('#water_raw_material_qty_dayErrorMsg').show();
                    $('#water_raw_material_qty_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_raw_material_qty_day').focus();
                }
                else if (water_required_value == 'Yes' && water_raw_material_recycle_day == "") {
                    $('#water_raw_material_recycle_dayErrorMsg').html("Please Select One.");
                    $('#water_raw_material_recycle_dayErrorMsg').show();
                    $('#water_raw_material_recycle_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_raw_material_recycle_day').focus();
                }
                else if (water_required_value == 'Yes' && water_cleaning_source == "") {
                    $('#water_cleaning_sourceErrorMsg').html("Please Select One.");
                    $('#water_cleaning_sourceErrorMsg').show();
                    $('#water_cleaning_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_cleaning_source').focus();
                }
                else if (water_required_value == 'Yes' && water_cleaning_qty_day == "") {
                    $('#water_cleaning_qty_dayErrorMsg').html("Please Select One.");
                    $('#water_cleaning_qty_dayErrorMsg').show();
                    $('#water_cleaning_qty_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_cleaning_qty_day').focus();
                }
                else if (water_required_value == 'Yes' && water_cleaning_recycle_day == "") {
                    $('#water_cleaning_recycle_dayErrorMsg').html("Please Select One.");
                    $('#water_cleaning_recycle_dayErrorMsg').show();
                    $('#water_cleaning_recycle_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_cleaning_recycle_day').focus();
                }
                else if (water_required_value == 'Yes' && water_process_source == "") {
                    $('#water_process_sourceErrorMsg').html("Please Select One.");
                    $('#water_process_sourceErrorMsg').show();
                    $('#water_process_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_process_source').focus();
                }
                else if (water_required_value == 'Yes' && water_process_qty_day == "") {
                    $('#water_process_qty_dayErrorMsg').html("Please Select One.");
                    $('#water_process_qty_dayErrorMsg').show();
                    $('#water_process_qty_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_process_qty_day').focus();
                }
                else if (water_required_value == 'Yes' && water_process_recycle_day == "") {
                    $('#water_process_recycle_dayErrorMsg').html("Please Select One.");
                    $('#water_process_recycle_dayErrorMsg').show();
                    $('#water_process_recycle_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_process_recycle_day').focus();
                }
                else if (water_required_value == 'Yes' && water_domestic_source == "") {
                    $('#water_domestic_sourceErrorMsg').html("Please Select One.");
                    $('#water_domestic_sourceErrorMsg').show();
                    $('#water_domestic_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_domestic_source').focus();
                }
                else if (water_required_value == 'Yes' && water_domestic_qty_day == "") {
                    $('#water_domestic_qty_dayErrorMsg').html("Please Select One.");
                    $('#water_domestic_qty_dayErrorMsg').show();
                    $('#water_domestic_qty_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_domestic_qty_day').focus();
                }
                else if (water_required_value == 'Yes' && water_dust_compression_source == "") {
                    $('#water_dust_compression_sourceErrorMsg').html("Please Select One.");
                    $('#water_dust_compression_sourceErrorMsg').show();
                    $('#water_dust_compression_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_dust_compression_source').focus();
                }
                else if (water_required_value == 'Yes' && water_dust_compression_qty_day == "") {
                    $('#water_dust_compression_qty_dayErrorMsg').html("Please Select One.");
                    $('#water_dust_compression_qty_dayErrorMsg').show();
                    $('#water_dust_compression_qty_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_dust_compression_qty_day').focus();
                }
                else if (water_required_value == 'Yes' && water_dust_compression_recycle_day == "") {
                    $('#water_dust_compression_recycle_dayErrorMsg').html("Please Select One.");
                    $('#water_dust_compression_recycle_dayErrorMsg').show();
                    $('#water_dust_compression_recycle_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_dust_compression_recycle_day').focus();
                }
                else if (water_required_value == 'Yes' && water_others_name == "") {
                    $('#water_others_nameErrorMsg').html("Please Select One.");
                    $('#water_others_nameErrorMsg').show();
                    $('#water_others_nameErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_others_name').focus();
                }
                else if (water_required_value == 'Yes' && water_others_source == "") {
                    $('#water_others_sourceErrorMsg').html("Please Select One.");
                    $('#water_others_sourceErrorMsg').show();
                    $('#water_others_sourceErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_others_source').focus();
                }
                else if (water_required_value == 'Yes' && water_others_qty_day == "") {
                    $('#water_others_qty_dayErrorMsg').html("Please Select One.");
                    $('#water_others_qty_dayErrorMsg').show();
                    $('#water_others_qty_dayErrorMsg').delay(2000).fadeOut('slow');
                    $('#water_others_qty_day').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "/road_project_details_two/",
                            data: $('#project_details_two_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#project_details_two_successMsg').html("Saved Successfully");
                                    $('#project_details_two_successMsg').show();
                                    $('#project_details_two_successMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_two_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#collapseSevenBtn").removeAttr("disabled");
                                        $("#collapseSeven").addClass("show");
                                        $("#collapseProjectTwo").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;

                                    $('#project_details_two_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#project_details_two_errorMsg').show();
                                    $('#project_details_two_errorMsg').focus();
                                    setTimeout(function () {
                                        $('#project_details_two_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }

            function save_road_anc_other_details() {
                let anc_other_required = $("input[name=anc_other_required]:checked").length;
                let anc_other_required_value = $("input[name=anc_other_required]:checked").val();

                if (anc_other_required < 1) {
                    $('#anc_other_requiredErrorMsg').html("Please Select One.");
                    $('#anc_other_requiredErrorMsg').show();
                    $('#anc_other_requiredErrorMsg').delay(2000).fadeOut('slow');
                    $('#anc_other_required').focus();
                }
                else if (anc_other_required_value == "Yes" && !$('#anc_other_bridge').is(":checked") && !$('#anc_other_crushing_unit').is(":checked") && !$('#anc_other_concrete_building').is(":checked") && !$('#anc_other_asphalt_plant').is(":checked") && !$('#anc_other_surface_collection').is(":checked") && !$('#anc_other_general').is(":checked")) {
                    $('#anc_others_errorMsg').html("Please select one ancillary.");
                    $('#anc_others_errorMsg').show();
                    $('#anc_others_errorMsg').delay(2000).fadeOut('slow');
                    $('.anc_others').focus();
                }
                else {
                    $.ajax
                        ({
                            type: "POST",
                            url: "{% url 'save_anc_other_details' %}",
                            data: $('#anc_others_form').serialize(),
                            success: function (data) {
                                if (data.message == 'success') {
                                    $('#anc_others_successMsg').html("Saved Successfully");
                                    $('#anc_others_successMsg').show();
                                    setTimeout(function () {
                                        $('#anc_others_successMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                    setTimeout(function () {
                                        $("#headingEightBtn").removeAttr("disabled");
                                        $("#collapseEight").addClass("show");
                                        $("#collapseSeven").removeClass("show");
                                    }, 2000);
                                }
                                else {
                                    var errorMsg = data.error;

                                    $('#anc_others_errorMsg').html(`Application Error: ${data.error}`);
                                    $('#anc_others_errorMsg').show();
                                    setTimeout(function () {
                                        $('#anc_others_errorMsg').delay(2000).fadeOut('slow');
                                    }, 2000);
                                }
                            }
                        });
                }
            }