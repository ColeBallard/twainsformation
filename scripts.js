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
        let newInput = createDepthControlInput();
        $('#inputContainer').append(newInput);
    });
});

function createDepthControlInput() {
    let inputGroup = $('<div>', { 'class': 'input-group mb-2' });

    let indentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '>',
        click: function() {
            adjustDepth(inputGroup, 20);
        }
    });

    let outdentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '<',
        click: function() {
            adjustDepth(inputGroup, -20);
        }
    });

    let input = $('<input>', {
        type: 'text',
        'class': 'form-control',
        placeholder: 'Enter detail'
    });

    inputGroup.append(outdentBtn, indentBtn, input);

    return inputGroup;
}

function adjustDepth(element, adjustment) {
    let currentPadding = parseInt(element.css('padding-left'), 10);
    element.css('padding-left', `${Math.max(0, currentPadding + adjustment)}px`);
}