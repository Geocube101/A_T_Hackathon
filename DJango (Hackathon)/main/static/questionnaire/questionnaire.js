const HOVER_FADE_TIME = 100;

function branch_option_exit(max_index)
{
    return new Promise(function (resolve, reject) {
        for (let index = 0; index < max_index; index++) {
            let node = document.getElementById(`branch_option_${index}`);

            if (node.style.display !== 'none') {
                window.setTimeout(function (id) {
                    $(`#${id}`).animate({'left': '5%'}, 250, function () {
                        $(`#${id}`).animate({'left': '100%'}, 750, function () {
                            if (index + 1 === max_index)
                            {
                                $('.branch_option').css('display', 'none');
                                resolve(undefined);
                            }
                        });
                    });
                }, 100 * index, node.id);
            }
        }
    });
}

function company_option_exit(max_index)
{
    return new Promise(function (resolve, reject) {
        for (let index = 0; index < max_index; index++) {
            let node = document.getElementById(`company_option_${index}`);

            if (node.style.display !== 'none') {
                window.setTimeout(function (id) {
                    $(`#${id}`).animate({'left': '5%'}, 250, function () {
                        $(`#${id}`).animate({'left': '100%'}, 750, function () {
                            if (index + 1 === max_index)
                            {
                                $('.company_option_exit').css('display', 'none');
                                resolve(undefined);
                            }
                        });
                    });
                }, 100 * index, node.id);
            }
        }
    });
}

function capitalize(string)
{
    let output = [];
    for (let seg of string.split(' ')) output.push(seg.charAt(0).toUpperCase() + seg.slice(1));
    return output.join(' ');
}

function fade_switch_title(msg)
{
    let fade0 = document.getElementById('title_fade_0');
    let fade1 = document.getElementById('title_fade_1');

    if (fade0.style.display === 'none')
    {
        fade0.innerText = msg;
        $(fade0).css('display', 'block');
        $(fade0).animate({'opacity': '1'}, 500);

        $(fade1).animate({'opacity': '0'}, 500, function(){
            $(this).css('display', 'none');
        });
    }
    else
    {
        fade1.innerText = msg;
        $(fade1).css('display', 'block');
        $(fade1).animate({'opacity': '1'}, 500);

        $(fade0).animate({'opacity': '0'}, 500, function(){
            $(this).css('display', 'none');
        });
    }
}

function on_search_input_change(element)
{
    //let node = document.getElementById(`branch_option_${index}`);
    let index = 0;
    let node = document.getElementById('branch_option_0');

    while (node != null)
    {
        let jobj = $(node);

        if (node.innerHTML.toLocaleLowerCase().indexOf(element.value.toLocaleLowerCase()) === -1)
        {
            jobj.animate({'opacity': 0, 'height': 0}, 250);
        }
        else
        {
            jobj.stop();
            jobj.animate({'opacity': 1, 'height': '2em'}, 250);
        }

        node = document.getElementById(`branch_option_${++index}`);
    }
}

function search(selected, max_index)
{
    let values = [];
    let res = null;
    for (let name of selected) values.push(document.getElementById(name).dataset.id);

    branch_option_exit(max_index).then(function(){
        let timer = window.setTimeout(function(){
            if (res != null)
            {
                window.clearTimeout(timer);
                let source = document.getElementById('content_box');
                let search_bar = $('#search_bar');
                let highest_index = 0;
                let elements = [];
                let companies = {}

                fade_switch_title('Choose your Intended Company');
                search_bar.attr('placeholder', 'Search Companies');
                search_bar.animate({'width': '30%'}, 250)

                for (let branch of Object.keys(res))
                {
                    let json = JSON.parse(res[branch]);
                    let keys = Object.keys(json.companies);
                    highest_index += keys.length;

                    for (let cid in keys)
                    {
                        let company = keys[cid];
                        let xml = new XMLHttpRequest();
                        companies[company] = json.companies[company];

                        xml.onreadystatechange = function()
                        {
                            if (xml.readyState === XMLHttpRequest.DONE)
                            {
                                if (xml.status === 200)
                                {
                                    console.log('Got');
                                    let node = document.createElement('div');
                                    let logo = document.createElement('img');
                                    let text = document.createElement('span');

                                    logo.src = "data:image/png;base64," + xml.response;
                                    text.innerHTML = capitalize(company);
                                    node.append(logo);
                                    node.appendChild(text);
                                    node.appendChild(document.createElement('hr'));
                                    node.className = 'company_option';
                                    node.style.left = '100%';
                                    node.id = `company_option_${cid}`;
                                    node.dataset.company = company;
                                    elements.push(node);
                                }
                                else
                                {
                                    alert('Request Failed');
                                }
                            }
                        }

                        xml.open('POST', '/get_web_logo');
                        xml.setRequestHeader('Content-Type', 'text/plain');
                        xml.send(JSON.stringify({'discipline': branch, 'company': company}));
                    }
                }

                let left_anim_timer = window.setInterval(function(){
                    if (elements.length === highest_index)
                    {
                        window.clearInterval(left_anim_timer);
                        for (let index in elements)
                        {
                            let elem = elements[index];
                            source.appendChild(elem);

                            window.setTimeout(function(id){
                                $(`#${id}`).animate({'left': '10%'}, 500);
                            }, 100 * index, elem.id);
                        }

                        window.setTimeout(companies_master, 100 * highest_index, highest_index, companies);
                    }
                }, 10);
            }
        }, 10);
    });
    let xml = new XMLHttpRequest();

    xml.onreadystatechange = function()
    {
        if (xml.readyState === XMLHttpRequest.DONE)
        {
            if (xml.status === 200)
            {
                res = JSON.parse(xml.response);
            }
            else
            {
                alert('Request Failed');
            }
        }
    }

    xml.open('POST', '/get_select_disciplines');
    xml.setRequestHeader('Content-Type', 'application/json');
    xml.send(JSON.stringify({'targets': values}));
}

function companies_master(max_index, data)
{
    const company_option_class = $('.company_option');

    company_option_class.on('click', function(event){
        let eid = event.currentTarget.id;
        company_option_exit(max_index).then(function(){
            company_enter(event.currentTarget.dataset.company, data[event.currentTarget.dataset.company]);
        });
    });

    company_option_class.hover(function(event){
        let id = `#${event.currentTarget.id}`;
        event.currentTarget.animate({'borderLeftColor': '#888888'}, HOVER_FADE_TIME);
        window.setTimeout(function(){
            $(id).css('borderLeftColor', '#888888');
        }, HOVER_FADE_TIME);
    }, function(event){
        let id = `#${event.currentTarget.id}`;
        event.currentTarget.animate({'borderLeftColor': 'purple'}, HOVER_FADE_TIME);
        window.setTimeout(function(){
            $(id).css('borderLeftColor', 'purple');
        }, HOVER_FADE_TIME);
    });
}

function company_enter(company, data)
{
    let question_box = $('#questionnaire');
    question_box.css('display', 'block');
    question_box.animate({'opacity': '1'}, HOVER_FADE_TIME);
    console.log(data);
}

function question_box_init()
{
    const SELECTED_OPTIONS = [];
    let HIGHEST_OPTION_INDEX;

    window.setTimeout(function(){
        $('#question_box').animate({'top': '10vh', 'opacity': '1'}, 1000, function(){
            for (let index = 0; index < HIGHEST_OPTION_INDEX; index++)
            {
                let node = document.getElementById(`branch_option_${index}`);

                window.setTimeout(function(id){
                    $(`#${id}`).animate({'left': '10%'}, 500);
                }, 100 * index, node.id);
            }

            const branch_option_class = $('.branch_option');

            branch_option_class.on('click', function(event){
                let eid = event.currentTarget.id;
                let index = SELECTED_OPTIONS.indexOf(eid);
                let search = $('#question_box_title').children('input')[0];

                search.value = '';
                on_search_input_change(search);

                if (index === -1)
                {
                    SELECTED_OPTIONS.push(event.currentTarget.id);
                    $(event.currentTarget).css({'borderLeftColor': 'blue'});
                }
                else
                {
                    SELECTED_OPTIONS.splice(index, 1);
                    $(event.currentTarget).css({'borderLeftColor': 'purple'});
                }
            });

            branch_option_class.hover(function(event){
                let id = `#${event.currentTarget.id}`;
                event.currentTarget.animate({'borderLeftColor': '#888888'}, HOVER_FADE_TIME);
                window.setTimeout(function(){
                    $(id).css('borderLeftColor', '#888888');
                }, HOVER_FADE_TIME);
            }, function(event){
                let id = `#${event.currentTarget.id}`;
                let color = (SELECTED_OPTIONS.indexOf(event.currentTarget.id) === -1) ? 'purple': 'blue';
                event.currentTarget.animate({'borderLeftColor': color}, HOVER_FADE_TIME);
                window.setTimeout(function(){
                    $(id).css('borderLeftColor', color);
                }, HOVER_FADE_TIME);
            });

            $('#question_box_title img').click(function(){
                search(SELECTED_OPTIONS, HIGHEST_OPTION_INDEX);
            });

            $(document).keyup(function(e){
                if (e.which === 13) search(SELECTED_OPTIONS, HIGHEST_OPTION_INDEX);
            });

            $('#question_box').focus();
        });
    }, 500);

    let xml = new XMLHttpRequest();

    xml.onreadystatechange = function()
	{
		if (xml.readyState === XMLHttpRequest.DONE)
		{
			if (xml.status === 200)
			{
			    let json = JSON.parse(xml.response);
                let branches = json.names;
                let keys = json.keys;
                let source = document.getElementById('content_box');
                HIGHEST_OPTION_INDEX = keys.length;

                for (let bid in branches)
                {
                    let node = document.createElement('div');
                    let text = document.createElement('span');
                    text.innerHTML = branches[bid];
                    node.appendChild(text);
                    node.appendChild(document.createElement('hr'));
                    node.className = 'branch_option';
                    node.style.left = '100%';
                    node.id = `branch_option_${bid}`;
                    node.dataset.id = keys[bid];
                    source.appendChild(node);
                }
			}
			else
			{
				alert('Request Failed');
			}
		}
	}

	xml.open('POST', '/get_disciplines');
	xml.setRequestHeader('Content-Type', 'text/plain');
	xml.send();
}