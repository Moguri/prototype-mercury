var data = {
};
function setup_ui(initial_state) {
    initial_state = initial_state || {};
    data.state = Object.assign({
      show_menu: false,
      menu_heading: '',
      menu_items: [],
      selection_index: 0,
      message: '',
      message_modal: '',
    }, initial_state);
    var app = new Vue({
        el: '#app',
        data: data
    });
}

function update_state(new_state) {
    data.state = Object.assign({}, data.state, new_state); 
}

