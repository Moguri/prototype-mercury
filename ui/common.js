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

Vue.component('nav-bar', {
  props: ['show_menu', 'menu_heading', 'menu_items', 'selection_index'],
  template: `
      <div id='nav' v-if='show_menu' class='pure-menu'>
          <span class='custom-menu-heading pure-menu-heading'>{{menu_heading}}</span>
          <ul class='pure-menu-list'>
              <li v-for='(item, idx) in menu_items' class='custom-menu-item pure-menu-item'
                  v-bind:class="{'pure-menu-selected': idx == selection_index}">
                  <a href='#' class='pure-menu-link'>{{item}}</a>
              </li>
          </ul>
      </div>
  `
});

Vue.component('message-bar', {
  props: ['message', 'modal'],
  template: `
    <div id='message-bar' v-if='message !== ""'>
        <span>{{message}}</span>
        <span class='modal-indicator' v-if='modal'>&#x25bc;</span>
    </div>
  `
});
