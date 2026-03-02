const menuBtn = document.getElementById('menuBtn');
const menuDropdown = document.getElementById('menuDropdown');

menuBtn.addEventListener('click', () => {
  menuDropdown.classList.toggle('active');
});

window.addEventListener('click', (e) => {
  if (!menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
    menuDropdown.classList.remove('active');
  }
});

const slides = document.querySelectorAll('.slide');
const progressBar = document.querySelector('.timer-progress');
const nextBtn = document.getElementById('nextSlide');
const prevBtn = document.getElementById('prevSlide');

let slideIndex = 0;
let slideInterval;

function updateSlide(index) {
    slides.forEach(s => s.classList.remove('active'));
    
    progressBar.style.transition = 'none';
    progressBar.style.width = '0%';
    
    setTimeout(() => {
        slides[index].classList.add('active');
        progressBar.style.transition = 'width 10000ms linear';
        progressBar.style.width = '100%';
    }, 50);

    slideIndex = index;
}

function moveNext() {
    let next = (slideIndex + 1) % slides.length;
    updateSlide(next);
}

function startTimer() {
    clearInterval(slideInterval);
    slideInterval = setInterval(moveNext, 10000); // 10 секунд
}

nextBtn.addEventListener('click', () => {
    moveNext();
    startTimer();
});

prevBtn.addEventListener('click', () => {
    let prev = (slideIndex - 1 + slides.length) % slides.length;
    updateSlide(prev);
    startTimer();
});

updateSlide(0);
startTimer();