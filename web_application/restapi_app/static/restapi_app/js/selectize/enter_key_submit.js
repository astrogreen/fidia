Selectize.define('enter_key_submit', function (options) {
    var self = this;

    this.onKeyDown = (function (e) {
        var original = self.onKeyDown;

        return function (e) {
            // this.items.length MIGHT change after event propagation.
            // We need the initial value as well. See next comment.
            var initialSelection = this.items.length;
            original.apply(this, arguments);

            if (e.keyCode === 13
                // Necessary because we don't want this to be triggered when an option is selected with Enter after pressing DOWN key to trigger the dropdown options
                && initialSelection && initialSelection === this.items.length
                && this.$control_input.val() === '') {
                self.trigger('submit');
            }
        };
    })();
});