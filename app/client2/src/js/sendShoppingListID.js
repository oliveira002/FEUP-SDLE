// sendShoppingListID.js
form = document.getElementById('shoppingListIDSubmit')
form.addEventListener('click', function() {
    event.preventDefault()
    let id = document.getElementById("shoppingListIDInput").value;
    if (id !== '') {
        window.ipcRenderer.send('submit-shoppingListID', id);
        console.log('Message sent to main process:', id);
    }
});
