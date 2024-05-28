document.addEventListener('DOMContentLoaded', function () {
    function isMobile() {
        return window.innerWidth <= 768;
    }

    function adjustForDevice() {
        const body = document.body;
        const messageBoard = document.querySelector('.message-board');
        const verifyButton = document.querySelector('.verify-button');

        if (isMobile()) {
            body.style.backgroundImage = "url('img/移动端背景图.jpg')";
            messageBoard.style.backgroundImage = "url('img/移动端白色方框.png')";
            verifyButton.style.backgroundImage = "url('img/移动端验证身份按钮.png')";
        } else {
            body.style.backgroundImage = "url('img/PC端背景图.jpg')";
            messageBoard.style.backgroundImage = "url('img/PC端白色方框.png')";
            verifyButton.style.backgroundImage = "url('img/PC端验证身份按钮.png')";
        }
    }

    window.addEventListener('resize', adjustForDevice);
    adjustForDevice();
});
