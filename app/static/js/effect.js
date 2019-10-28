/*!
 * PICLine Effect (https://zhiz.xyz)
 * Copyright 2019 ZHZI.
 */
const MOBILE_WIDTH = 650
$(function(){
    // $('body').niceScroll({ cursorcolor: '#2C3E50' });
    $.ajaxSetup({
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            MsgFlash({
                text: '服务器出现未知错误，请稍后重试',
                icon: 'err',
                effect: 'shake'
            });
        }
    });

    $(window).scroll(function () {
        const top = $(document).scrollTop();
        // Header Fixed
        if (top >= $('header.header').height()) {
            $('nav.menu').addClass('menu-fixed');
            $('header.header').css('margin-bottom', $('nav.menu').outerHeight() + 'px');
        }else {
            $('nav.menu').removeClass('menu-fixed');
            $('header.header').css('margin-bottom', '0px');
        }
        // Top Fixed
        if (top >= 100) {
            $('#top').fadeIn();
        }else {
            $('#top').fadeOut();
        }
    });

    //自动按钮loadding配置
    $('.btn-loading').on('click', function () {
        $(this).data('original_text', $(this).text());
        $(this).html('<svg class="icon rotate"><use xlink:href="#iconloading1"></use></svg>').addClass('disabled').attr('disabled', 'disabled');
    });
    //手动按钮loadding配置
    //state = true 锁定, 不写或false解锁
    jQuery.fn.setLoading = function (state) {
        if (state) {
            $(this).data('original_text', $(this).text());
            $(this).html('<svg class="icon rotate"><use xlink:href="#iconloading1"></use></svg>').addClass('disabled').attr('disabled', 'disabled');

        } else {
            let original_text = $(this).data('original_text');
            if (original_text) {
                $(this).html(original_text).removeClass('disabled').removeAttr('disabled');
                $(this).removeData('original_text');
            }
        }
    }
    //设置成功按钮
    jQuery.fn.setOK = function (delay=1000, callback) {
        $(this).html('<svg class="icon fadeIn"><use xlink:href="#iconchenggong"></use></svg>');
        setTimeout(callback, delay);
    }

    $('.articles').on('click', '.view-full', function () {
        const $cover = $(`<div class="full-cover"><div class="full-content"><img class="loading" src="/static/img/loading-1.svg"></div>`);
        const $content = $cover.find('.full-content');
        const $img = $(`<img class="full-img" src="${$(this).attr('src')}">`);
        $('body').append($cover);
        $content.append($img);
        $img.on('load', function () {
            $content.css({
                'width': ($(window).width() <= MOBILE_WIDTH ? '100%' : $img.width() + 'px'),
                'height': ($(window).width() <= MOBILE_WIDTH ? 'auto' : $img.height() + 'px')
            })
            if($img.height() > $cover.height()) {
                $content.css({'transform': 'translate(-50%, 0)', 'top': '5%'});
                $cover.css({ 'position': 'absolute', 'height': '100%' });
            }
        });
        $cover.on('click', function () {
            $cover.fadeOut(200);
            setTimeout(() => {
                $cover.remove();
            }, 200)
        });
    });
    //设置昵称
    $('#set_nickname').click(function () {
        $('.set-nickname').show();
    });
    $('#nickname_cancel').click(function () {
        $('.set-nickname').hide();
    });
    $('#nickname_commit').click(function () {
        const $this = $('#nickname');
        const nickname = $this.val().trim();

        if (nickname.length >= 2 && nickname.length <= 8) {
            $('#nickname_commit').setLoading(true);
            $.post('/user/set-nickname/', {nickname}, function (res) {
                HandleRes(res, () => {
                    $('.register .username').removeClass('form-error');
                    $('#nickname_cancel').click();
                    $('.set-nickname').remove();
                    $('#nickname_line').text('昵称：' + nickname);
                    MsgFlash('设置昵称成功');
                }, () => {
                    $this.parent().addClass('form-error');
                    $this.parent().find('.form-error-msg').text('昵称已被使用');
                })
                $('#nickname_commit').setLoading(false);
            });
        } else {
            $this.parent().addClass('form-error');
            $this.parent().find('.form-error-msg').text('昵称为2~8位');
        }
    });
    //点赞
    //喜欢
    $('.articles').on('click', '.like, .fav',function (e) {
        if ($(this).hasClass('disabled') || $(this).text().indexOf('已')>-1) return;
        if ($(this).attr('disabled') == 'disabled') return;
        const $this = $(this);
        const type = $(this).attr('class');
        const comment_id = $(this).data('comment_id');
        const article_id = $(this).data('id') + '';

        //点赞
        if (type == 'like') {
            //let liked_str = window.localStorage.getItem('HLDPIC:liked');
            // if (liked_str) {
            //     let liked_list = liked_str.split(',');
            //     if (liked_list.indexOf(article_id) > -1) {
            //         MsgFlash('已经点过赞啦');
            //         return;
            //     }
            // }
            let replace_word = '赞';
            if ($(this).html().indexOf('赞一个') >= 0) {
                replace_word = '赞一个';
            }
            //show +1
            const $click_label = $('<span>+1</span>');
            const mouse_x = e.pageX;
            const mouse_y = e.pageY;
            $click_label.css({
                'position': 'absolute',
                'top': (mouse_y - 20) + 'px',
                'left': mouse_x + 'px',
                'color': 'red',
                'font-size': '20px',
                'font-weight': 'bold'
            });
            $('body').append($click_label);
            $click_label.animate({
                'top': (mouse_y - 40) + 'px',
                'opacity': '0'
            }, 1000, () => {
                $click_label.remove();
            });
            // count + 1
            if ($this.data('type') == 'count') {
                let current_count = +$(this).find('.like-count').text();
                $(this).find('.like-count').text(current_count+1);
            }

            $(this).html($(this).html().replace(replace_word, '已赞'));
            let data = { article_id, comment_id, type};
            $.post('/statistics/', data, function(){
                $this.attr('disabled', 'disabled');
                // if (liked_str) {
                //     let liked_list = liked_str.split(',');
                //     if (liked_list.indexOf(article_id) == -1) {
                //         liked_list.push(article_id);
                //         window.localStorage.setItem('HLDPIC:liked', liked_list.join(','));
                //     }
                // } else {
                //     window.localStorage.setItem('HLDPIC:liked', article_id);
                // }
            })
        }
        //收藏
        if (type == 'fav') {
            $.post('/favorite/', { article_id, command: 'add' }, (res) => {
                if(res.code == 401) {
                    $('.login-form').show();
                    return;
                }
                $(this).html($(this).html().replace('收藏', '已收藏'));
                HandleRes(res, () => {
                }, () => {
                    MsgFlash('此文章已经在收藏列表中');
                })
            })
        }
        e.preventDefault();
        return false;
    });
    //打赏
    $('.articles').on('click', '.reward', function (e) {
        MsgFlash('您的心意已经收到了呢~')
    });

    //加载更多
    $('.articles').on('click', '.load-more', function () {
        const $this = $(this);
        const next_page = $this.data('next');
        const q = window.location.search;
        $this.addClass('is-loading');
        $.get(`/article-load-more/${q}`, {
            page: next_page
        }, (res) => {
            $('.load-more').removeClass('is-loading');
                $this.after(res);
                $this.remove();
                // $('body').getNiceScroll().resize();
        })
    });

    //搜索框
    $('#search, #search_close').click(function () {
        $('.search-bar').slideToggle(150);
    });
    //搜索
    $('#search_btn').click(function () {
        const keywords = $('#search_keyword').val().trim();
        if (keywords != '') {
            window.location.href = '/query/?keywords=' + keywords;
        }
    });
    $('#search_keyword').keypress(function (e) {
        var eCode = e.keyCode ? e.keyCode : e.which ? e.which : e.charCode;
        if (eCode == 13) {
            $('#search_btn').click();
        }
    })
    //返回顶部
    $('#top').click(function () { ToAP('body', 500) });

    //Tab
    $('.tab-title > li').click(function(){
        $('.tab-title > li').removeClass();
        $(this).addClass('active');
        const $panels = $(this).parent().siblings('.tab-content');
        $panels.children('div').hide();
        const $target = $panels.children('div:eq(' + $(this).index() + ')');
        $(this).parents('.login-wrap').removeClass('login register').addClass($target.attr('class'));
        $target.show(200);
    });

    //跳转注册
    $('#register_tab').click(function () {
        $('.tab-title li:last-child').click();
    });

    //Login
    $('.login-show').click(function () {
        if ($('.login-form').length > 0) {
            $('.login-form').show();
        }else {
            window.location.href = '/?state=login'
        }  
    });
    //关闭注册窗口
    $('.login-close').click(function () {
        $('.login-form').fadeOut(200);
    });

    /**
     * 表单验证
     */
    //注册账号验证
    $('#register_username').blur(function () {
        const $this = $(this);
        const username = $this.val();
        const reg = /^[a-zA-Z0-9_-]{8,20}$/;
        if (username.match(reg)){
            $.get('/user/check/?username=' + username, function (res) {
                HandleRes(res, () => {
                    $('.register .username').removeClass('form-error');
                }, () => {
                    $this.parent().addClass('form-error');
                    $this.parent().find('.form-error-msg').text('用户名已被使用');
                })
            });
        }else {
            $this.parent().addClass('form-error');
            $this.parent().find('.form-error-msg').text('用户名长度或字符无效');
        }
    });

    //注册邮箱验证
    $('#register_email').blur(function () {
        const $this = $(this);
        const reg = /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
        if ($this.val().match(reg)) {
            $.get('/user/check/?email=' + $this.val(), function (res) {
                HandleRes(res, () => {
                    $this.parent().removeClass('form-error');
                }, () => {
                    $this.parent().addClass('form-error');
                    $this.parent().find('.form-error-msg').text('邮箱已被使用');
                })
            });
        } else {
            $this.parent().addClass('form-error');
            $this.parent().find('.form-error-msg').text('邮箱格式不正确');
        }
    });

    //注册密码验证
    $('#register_passwd').blur(function () {
        const reg = /^[a-zA-Z0-9_-]{6,20}$/;
        if ($(this).val().match(reg)) {
            $(this).parent().removeClass('form-error');
        } else {
            $(this).parent().addClass('form-error');
            $(this).parent().find('.form-error-msg').text('密码长度或字符无效');
        }
    });


    //注册密码验证-repeat
    $('#register_passwd_repeat').blur(function () {
        const reg = /^[a-zA-Z0-9_-]{6,20}$/;
        if ($(this).val().match(reg)) {
            const passwd = $('#register_passwd').val();
            if($(this).val() == passwd) {
                $(this).parent().removeClass('form-error');
            }else {
                $(this).parent().addClass('form-error');
                $(this).parent().find('.form-error-msg').text('两次密码输入不一致');
            }
        } else {
            $(this).parent().addClass('form-error');
            $(this).parent().find('.form-error-msg').text('密码长度或字符无效');
        }
    });
    //登录
    $('#login_btn').click(function () {
        const login_username = $('#login_user').val().trim();
        const login_passwd = $('#login_passwd').val().trim();
        if (login_username == '' || login_passwd == '') {
            MsgFlash('账号或密码不能为空');
            return;
        }
        $('#login_btn').setLoading(true);
        $.post('/user/login/', { login_username, login_passwd}, function (res) {
            $('#login_btn').setLoading(false);
            HandleRes(res, () => {
                $('#login_btn').setOK(500, function(){
                    window.location.reload();
                });
            });
        });
    });
    $('#login_passwd').keypress(function (e) {
        var eCode = e.keyCode ? e.keyCode : e.which ? e.which : e.charCode;
        if (eCode == 13) {
            $('#login_btn').click();
        }
    })

    //找回密码验证邮箱
    const set_Timer = (time) => {
        $('.success-tip').show();
        const current = Math.round((time - new Date().getTime()) / 1000);
        $('#send_verify_mail').text(`${current}秒后重新发送`);
        const timer = setInterval(() => {
            const now = new Date().getTime();
            const c = Math.round((time - now) / 1000);
            if (c > 0) {
                $('#send_verify_mail').text(`${c}秒后重新发送`);
            } else {
                $('#send_verify_mail').setLoading(false);
                $('#send_verify_mail').text('发送邮件');
                clearInterval(timer);
                window.localStorage.removeItem('reset_pwd_timer');
            }
        }, 1000);
    }
    if ($('#send_verify_mail').length > 0) {
        let one_min = window.localStorage.getItem('reset_pwd_timer');
        if (one_min) {
            one_min = +one_min;
            if (one_min - new Date().getTime() < 0) {
                window.localStorage.removeItem('reset_pwd_timer');
            }else {     
                set_Timer(one_min);
            }
        }
    }
    $('#send_verify_mail').click(function () {

        const email = $('#verify_mail').val();
        const reg = /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
        const reset_btn = () => {
            $('#send_verify_mail').setLoading(false);
            $('#send_verify_mail').text('发送邮件');
        }
        if (email.match(reg)) {
            //ajax
            $(this).setLoading(true);
            $.post('/user/verify-email/', { email})
            .then((res) => {
                if(res.code == 200) {
                    const one_min = new Date().getTime() + 1000 * 60;
                    window.localStorage.setItem('reset_pwd_timer', one_min);
                    set_Timer(one_min);
                } else if (res.code == 429) {
                    reset_btn();
                    MsgFlash({
                        text: '访问过于频繁，请稍后再试',
                        icon: 'err'
                    })
                } else if (res.code == 404) {
                    reset_btn();
                    MsgFlash({
                        text: '邮箱不存在',
                        icon: 'err'
                    })    
                }
            })
        }else {
            MsgFlash('邮箱格式有误')
        }
    });
    //重置密码
    $('#reset_password_btn').click(function () {
        const reg = /^[a-zA-Z0-9_-]{6,20}$/;
        const pwd = $('#reset_password').val();
        const pwd_repeat = $('#reset_password_repeat').val();
        if (pwd.match(reg)) {
            if (pwd == pwd_repeat) {
                $('#reset_password_btn').setLoading(true);
                $.post(window.location.href, {pwd})
                .then((res) => {
                    HandleRes(res, () => {
                        $('.reset-form').remove();
                        $('.reset-success').show();
                    })
                })
            }else {
                MsgFlash('两次输入密码不一致');
            }
        } else {
            MsgFlash('密码为6~20位英文数字');
        }
    });
    


    //注销
    $('#logout').click(function () {
        $.post('/user/logout/', function (res) {
            MsgFlash({
                text: '退出登录成功',
                icon: 'ok',
                callback: () => {
                    window.location.reload();
                }
            })
        });
    });

    $('#register_commit').click(function () {
        RegisterUser();
    });


    //修改头像
    $("#change_avatar").on("change", function (e) {
        $('#cropper_btn').setLoading(false);
        const file = $(this).get(0).files[0];
        let reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (e) => {
            const $image = $('#cropper_img');
            const imgbase64 = e.target.result;
            $image.attr('src', imgbase64);
            $image.cropper('destroy');
            $image.cropper({
                aspectRatio: 1
            });

            $('.cropper-img').fadeIn();
        }
    });
    $('#cropper_btn').click(function () {
        var cropper = $('#cropper_img').data('cropper');

        // $('#cropper_img').cropper('getCroppedCanvas', {
        //     width: 200, // 裁剪后的长宽
        //     height: 200
        // }).toBlob(function (blob) {
            
        // });
        $('#cropper_btn').setLoading(true);
        
        // setTimeout(() => {
        //     $('#cropper_cancel').click();
        // }, 2000);
        
        // Upload cropped image to server if the browser supports `HTMLCanvasElement.toBlob`

        const avatar_base64 = cropper.getCroppedCanvas().toDataURL('image/jpeg', 0.7);

        $.post('/user/set-avatar/', {avatar_base64}, (res) => {
            HandleRes(res, () => {
                $('#upload_avatar').attr('src', avatar_base64);
                $('.cropper-img').fadeOut();
                MsgFlash('修改头像成功');
            })
        });
    });
    $('#cropper_cancel').click(function () {
        $(this).removeAttr('disabled').html('上传');
        $('.cropper-img').fadeOut();
    });
    //填充匿名用户信息
    if ($('#guest_name').length > 0 && window.localStorage.getItem('guest_name')) {
        $('#guest_name').val(window.localStorage.getItem('guest_name'));
    }
    if ($('#guest_email').length > 0 && window.localStorage.getItem('guest_email')) {
        $('#guest_email').val(window.localStorage.getItem('guest_email'));
    }
    //提交评论
    $('#comment_submit').click(function () {

        let comment_content = $('#comment_content').val().trim();
        const article_id = $(this).data('id');
        let data = { article_id};
        //Guest
        if ($('.submit-comment .guest').length > 0) {
            const guest_name = $('#guest_name').val().trim();
            const guest_email = $('#guest_email').val().trim();
            var name_reg = /[@#\$%\^&\*]+/g;
            if (guest_name == '' || guest_name.length < 2 || guest_name.length > 8) {
                MsgFlash({
                    text: '请输入2~8个字之间的昵称',
                    effect: 'shake'
                });
                return;
            }
            if (guest_name.match(name_reg)) {
                MsgFlash({
                    text: '昵称中不能包含特殊符号',
                    effect: 'shake'
                });
                return;
            }

            if (guest_email != '') {
                const email_reg = /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
                if (!guest_email.match(email_reg)) {
                    MsgFlash({
                        text: '请输入正确的邮箱地址',
                        effect: 'shake'
                    });
                    return;
                }
                window.localStorage.setItem('guest_email', guest_email);
            }
            data['guest_name'] = guest_name;
            window.localStorage.setItem('guest_name', guest_name);
            data['guest_email'] = guest_email;
        }

        if (comment_content == '') {
            MsgFlash({
                text: '请输入评论内容',
                icon: 'info',
                effect: 'shake'
            });
            return;      
        }
        data['comment_content'] = comment_content;

        //检查回复
        if ($('.reply-msg > span').length > 0) {
            data['reply_id'] = $('.reply-msg > span').data('reply-id');
        }
        $('#comment_submit').setLoading(true);
        $.post('/comment/submit/', data, function (res) {
            HandleRes(res, () => {
                $('#comment_submit').setLoading(false);
                //$('#guest_name').val('');
                //$('#guest_email').val('');
                $('#comment_content').val('');
                $('.reply-msg').empty();
                MsgFlash({
                    text: '评论成功',
                    icon: 'ok'
                });
            });
        });
        
    });


    //回复
    $('.comment .reply').click(function () {
        const reply_id = $(this).data('reply-id');
        const reply_name = $('#c_' + reply_id).text();
        $('.reply-msg').empty();
        $('.reply-msg').append(`<span data-reply-id="${reply_id}">回复 ${reply_name} <svg class="icon"><use xlink:href="#iconguanbi"></use></svg> </span>`)
        ToAP('#comment_content');
    });
    //取消回复
    $('.reply-msg').on('click', 'svg', function () {
        $('.reply-msg').empty();
    });

    //回复重组
    if ($('.comments .comment').length > 0) {
        $('.comments .comment').each(function () {
            const reply_to = +$(this).data('reply');
            if (reply_to > 0){
                let g = '';
                const $reply_dom = $('#comment_' + reply_to);
                if($reply_dom.length > 0){
                    g = `<div class="reply-text"><div class="name"><a href="#">${$('#c_' + reply_to).text()}</a></div><div class="text">${$reply_dom.find('.text').html()}</div></div>`; 
                }else {
                    g = `<div class="reply-text"><div class="text muted">该评论由于触发关键字已被删除</div></div>`;
                }
                
                $(this).find('.text').prepend(g);
            }
        });
    }

    //用户详情入口
    $('.user-panel').mouseover(function () {
        if ($('.user-setting').is(':hidden')){
            $('.user-setting').show();
            setTimeout(() => {
                $('body').bind('click', function (e) {
                    if ($(e.target).parent().attr('class') != 'user-setting') {
                        $('body').unbind('click');
                        $('.user-setting').hide();
                    }
                });
            }, 10);
        }
    });
    //分页控制
    $('.async_container').on('click', '.pagination>ul a', function () {
        const url = $(this).attr('href');
        const el = $(this).parents('.async_container').attr('id');
        UserInfoDateLoading('#'+el, url);
        return false;
    });

    //移除收藏
    $('.async_container').on('click', 'li span', function () {
        const $a = $(this).siblings('a');
        const article_id = $a.data('id');
        $.post('/favorite/', { article_id, command: 'remove'}, (res) => {
            HandleRes(res, () => {
                $a.remove();
            });
        });
    });
    //已读
    $('.async_container').on('click', '.unread>a', function () {
        $(this).parent().removeClass('unread');
        $.post('/notice/', { id: $(this).data('id') });
    });
    $('.async_container').on('click', '.read-all', function () {
        const $notice = $('#notice_ul>li.unread');
        if ($notice.length > 0) {
            $notice.removeClass('unread');
            $.post('/notice/');
        }
        return false;
    });

    //浏览状态
    if (GetQueryString('state') == 'login') {
        if ($('.login-form').length > 0) {
            $('.login-form').show();
        }
    }
    
}())

//公共函数

//信息框
/**
 * 信息框闪烁
 * text: 文字
 * icon: 图标
 *   预设: ok  对号
 *        err  叉号
 *        info 问号
 * delay：延迟自动关闭
 * effect: 动画入场效果
 *    scale     缩放 默认
 *    shake     抖动
 * callback：自动关闭后回调函数
 */
function MsgFlash(setting) {
    
    let text = '';
    let delay = 2000;
    let icon = '';
    let effect = 'scale';
    let $dom = $(`<div class="layer-msg"><div class="msg-content"></div></div>`);
    if (setting instanceof Object) {
        text = setting.text || '';
        delay = setting.delay || 2000;
        icon = setting.icon || '';
        effect = setting.effect || 'scale';
    }else {
        text = setting;
    }
    if (icon != '') {
        let svg_icon = '';
        if (icon == 'ok') {svg_icon = 'iconchenggong' }
        else if (icon == 'err') {svg_icon = 'iconguanbi'}
        else if (icon == 'info') { svg_icon = 'iconinfo' }
        else { svg_icon = icon}
        $dom.find('.msg-content').append(`<div class="icon"><svg class="icon"><use xlink:href="#${svg_icon}"></use></svg></div>`);
    }
    if(text != '') {
        $dom.find('.msg-content').append(`<div class="text">${text}</div>`);
    }
    //播放结束
    const finish = () => {
        $dom.find('.msg-content').css('animation', 'msg-scale-out .3s');
        setTimeout(() => { $dom.remove() }, 250)
        if (setting.callback) setting.callback();
    }

    $dom.find('.msg-content').css('animation', `msg-${effect}-in .3s`);
    $('body').append($dom);
    const timer = setTimeout(() => {
        finish();
    }, delay-300);

    $dom.bind('click', function () {
        $dom.unbind('click');
        clearTimeout(timer);
        finish();
    });

}


//跳转到锚点
function ToAP(el, delay = 200) {
    if (!$(el)) return;
    $('html, body').animate({ scrollTop: $(el).offset().top }, delay);
}


//验证文件
function VerifyFile(file, format, size = null) {
    let msg = "";
    const suffix = file.name.substring(file.name.lastIndexOf('.') + 1);
    if (format.indexOf(suffix.toLowerCase()) == -1) {
        msg = "ERROR_FORMAT";
    }
    if (size) {
        let fileSize = Math.round(image.size / 1024 * 100) / 100;
        if (fileSize >= size) {
            msg = 'OVER_SIZE';
        }
    }

    return msg;
}

//注册用户
function RegisterUser(){

    let has_error = false;
    const register_Invitation_code = $('#register_Invitation_code').val().trim();
    const register_username = $('#register_username').val().trim();
    const register_email = $('#register_email').val().trim();
    const register_passwd = $('#register_passwd').val().trim();
    //检查空值
    if (register_Invitation_code =='' ||
        register_username == '' ||
        register_email == '' ||
        register_passwd == '') {
        has_error = true;
        }

    //检查错误
    $(".register > div").each(function(){
        if($(this).hasClass('form-error')) {
            has_error = true;
        }
    });

    if (has_error) {
        MsgFlash({
            text: '请正确填写所有信息',
            icon: 'info',
            effect: 'shake'
        })
    }else {
        $('#register_commit').setLoading(true);
        $.post('/user/register/', {
            register_Invitation_code,
            register_username,
            register_email,
            register_passwd
        }, function (res) {
            $('#register_commit').setLoading(false);
            HandleRes(res, () => {
                $('#register_commit').setOK();
                MsgFlash({
                    text: '注册成功',
                    icon: 'ok',
                    callback: function () {
                        window.location.reload();
                    }
                });
            });
        });
    }
}

//数据处理
function HandleRes(res, success, failed, error) {
    if (res.code == 200) {
        success(res);
    } else if (res.code == 400) {
        if (failed) {
            failed(res);
        } else {
            MsgFlash({
                text: res.msg,
                icon: 'err',
                effect: 'shake'
            });
        }
    } else if (res.code == 429){
        MsgFlash({
            text: '访问过于频繁，请稍后再试',
            icon: 'err'
        })
    } else {
        if (error) {
            error(res);
        } else {
            MsgFlash({
                text: '服务器出现未知错误，请稍后重试',
                icon: 'err',
                effect: 'shake'
            });
        }

    }
}

//个人信息数据载入
function UserInfoDateLoading(el, url) {
    //收藏
    $(el).html('<div class="loading"><img src="/static/img/loading-1.svg"></div>');
    $.get(url, (res) => {
        $(el).html(res);
    })
}

//获取当前路由参数
function GetQueryString(name) {
	var url = decodeURI(window.location.search.replace(/&amp;/g, "&"));
	var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
	var r = url.substr(1).match(reg);
	if(r != null) return unescape(r[2]);
	return null;
}
