let api;
const appState = {
    editor: null,
    gdb: {}
};

const vm = Vue.createApp({
    data: () => appState,
    methods: {
        loadEditor: (dataType, item) => {
            fetch(`/schema/${dataType}`)
                .then((response) => response.json())
                .then((schema) => {
                    const el = document.getElementById('editor');
                    if (appState.editor) {
                        appState.editor.destroy();
                    }
                    delete schema.links;
                    appState.editor = new JSONEditor(el, {
                        theme: 'bootstrap4',
                        schema,
                        startval: item,
                        compact: true,
                        show_errors: 'always',
                        disable_edit_json: true,
                        disable_collaps: true
                    });
                })
                .catch((e) => {
                    console.error(`Error loading editor: ${e.stack}`);
                });
        }
    }
});

fetch('/gdb')
    .then(response => response.json())
    .then((gdb) => {
        appState.gdb = gdb;
    })
    .then(() => vm.mount('#app'));
