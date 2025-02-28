document.getElementById('contactForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // You can add code here to handle form submission, e.g., send data to the server
    // For simplicity, let's just log the form data to the console.
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    
    console.log('Form submitted:', { name, email });
});

