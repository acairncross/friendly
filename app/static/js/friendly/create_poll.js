<script>
    function createNewPoll() {
        $.get("{{ url_for('static', filename='templates/poll_template.mustache') }}", function(template) {

            var pollNumContainer = document.getElementById('num-polls');
            var pollNum = pollNumContainer.value;

            var rendered = Mustache.render(template, {pollNum: pollNum});

            $("#polls").append(rendered);

            $("#add-choice" + pollNum).on("click", function() {
                createNewChoice(pollNum);
            });

            pollNumContainer.value++;

        });
    }

    function createNewChoice(pollNum) {
        $.get("{{ url_for('static', filename='templates/choice_template.mustache') }}", function(template) {
            var rendered = Mustache.render(template, {pollNum: pollNum});

            $("#poll" + pollNum).append(rendered);
        });
    }

    $(function() {

        $("#start-datetime").datetimepicker();
        $("#end-datetime").datetimepicker();
        createNewPoll();

        $("#add-poll").on("click", function(e) {
            createNewPoll();
        });

    });
</script>

