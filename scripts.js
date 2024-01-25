$(document).ready(function () {
    $('#style-changer-form').on('submit', function (e) {
        e.preventDefault();

        // Clear previous error messages
        $('.error').text('');

        // Validation
        let isValid = true;
        if ($('#fileUpload').val() === '') {
            $('#fileError').text('Please upload a file.');
            isValid = false;
        }
        if ($('#title').val().trim() === '') {
            $('#titleError').text('Please enter a title.');
            isValid = false;
        }
        if ($('#author').val().trim() === '') {
            $('#authorError').text('Please enter an author.');
            isValid = false;
        }
        if ($('#prompt').val().trim() === '') {
            $('#promptError').text('Please enter a prompt.');
            isValid = false;
        }

        if (!isValid) {
            return; // Stop the function if validation fails
        }

        var formData = new FormData(this);
        var fileInput = document.getElementById('fileUpload');
        formData.append("file", fileInput.files[0]);

        $.ajax({
            type: 'POST',
            url: '/style-changer', // Your Flask endpoint
            data: formData,
            contentType: false,
            processData: false,
            success: function (response) {
                // Assuming the response is the text you want to display
                $('#style-changer-response').html(response);
            },
            error: function (xhr, status, error) {
                // Handle any errors here
                console.error("Error: " + error);
                $('#style-changer-response').html("An error occurred: " + error);
            }
        });
    });

    $('#style-changer-tab').click(function(e) {
        e.preventDefault();
        $('#style-changer').show();
        $('#book-writer').hide();
        $('#book-condenser').hide();
        $(this).addClass('active');
        $('#book-writer-tab').removeClass('active');
        $('#book-condenser-tab').removeClass('active');
    });

    $('#book-writer-tab').click(function(e) {
        e.preventDefault();
        $('#style-changer').hide();
        $('#book-writer').show();
        $('#book-condenser').hide();
        $(this).addClass('active');
        $('#style-changer-tab').removeClass('active');
        $('#book-condenser-tab').removeClass('active');
    });

    $('#book-condenser-tab').click(function(e) {
        e.preventDefault();
        $('#style-changer').hide();
        $('#book-writer').hide();
        $('#book-condenser').hide();
        $(this).addClass('active');
        $('#book-writer-tab').removeClass('active');
        $('#style-changer-tab').removeClass('active');
    });

    $('#style-changer').hide();
    $('#book-writer').hide();
    $('#book-condenser').hide();

    $('#addInputBtn').click(function() {
        addInputField();
        updateLevels();
    });

    $('#book-writer-form').on('submit', function (e) {
        e.preventDefault();

        // Clear previous error messages
        $('.error').text('');

        // Validation
        let isValid = true;

        if ($('#book-writer-title').val().trim() === '') {
            $('#book-writer-title-Error').text('Please enter a title.');
            isValid = false;
        }

        if (!isValid) {
            return; // Stop the function if validation fails
        }

        let formData = {'outline': gatherFormData(), 'title': $('#book-writer-title').val().trim()};

        console.log(formData);
    
        $.ajax({
            type: "POST",
            url: "/book-writer",
            contentType: "application/json",
            data: JSON.stringify(formData),
            success: function(response) {
                console.log("Data submitted successfully:", response);
            },
            error: function(xhr, status, error) {
                console.error("Error in data submission:", xhr.responseText);
            }
        });
    });
});

function addInputField() {
    let newInput = createDepthControlInput();
    $('#inputContainer').append(newInput);
}

function createDepthControlInput() {
    let inputGroup = $('<div>', { 
        'class': 'input-group mb-2', 
        'data-depth': '1',
        css: { 'padding-left': '20px' }
    });

    let levelIndicator = $('<div>', {
        'class': 'level-indicator',
        css: { 'margin-right': '10px' }
    });

    let indentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '>',
        click: function() {
            adjustDepth(inputGroup, true);
        }
    });

    let outdentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '<',
        click: function() {
            adjustDepth(inputGroup, false);
        }
    });

    let deleteBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-danger',
        text: 'X',
        click: function() { deleteInputField(inputGroup); } // Corrected event handler
    });

    let input = $('<input>', {
        type: 'text',
        'class': 'form-control',
        placeholder: 'Enter detail'
    });

    inputGroup.append(levelIndicator, outdentBtn, indentBtn, input, deleteBtn);

    return inputGroup;
}

function adjustDepth(element, isIndent) {
    let currentDepth = parseInt(element.attr('data-depth'));
    currentDepth += isIndent ? 1 : -1;
    currentDepth = Math.max(1, currentDepth); // Ensure depth is not negative
    element.attr('data-depth', currentDepth.toString());

    // Adjust padding based on depth
    let padding = (20 * currentDepth);
    element.css('padding-left', `${padding}px`);

    updateLevels();
}

function updateLevels() {
    let levelNumbers = [0]; // Initialize level numbers

    $('#inputContainer').children('.input-group').each(function() {
        let depth = parseInt($(this).attr('data-depth'));

        while (levelNumbers.length - 1 > depth) {
            levelNumbers.pop(); // Remove deeper levels
        }
        if (levelNumbers.length - 1 < depth) {
            levelNumbers.push(1); // Start a new sub-level
        } else {
            levelNumbers[depth]++; // Increment the current level
        }

        let levelString = levelNumbers.slice(1).join('.');
        $(this).find('.level-indicator').text(levelString);
    });
}

function deleteInputField(element) {
    element.remove();
    updateLevels();
}

function gatherFormData() {
    let inputData = [];

    $('#inputContainer').find('.input-group').each(function() {
        let level = $(this).find('.level-indicator').text();
        let value = $(this).find('input[type="text"]').val();

        inputData.push({ value: value, level: level });
    });

    return inputData;
}

