async function askAI(){

let question=document.getElementById("question").value

document.getElementById("answer").innerHTML="AI thinking..."

let response=await fetch("http://localhost:5000/ask",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({question:question})

})

let data=await response.json()

document.getElementById("answer").innerHTML=data.answer

}

function startVoice(){

alert("Voice recognition activated")

}

async function loadQuiz(){

let response=await fetch("http://localhost:5000/quiz")

let data=await response.json()

document.getElementById("question").innerText=data.question

let optionsHTML=""

data.options.forEach((option,i)=>{

optionsHTML+=`<button onclick="checkAnswer(${i},${data.answer})">${option}</button><br><br>`

})

document.getElementById("options").innerHTML=optionsHTML

}

function checkAnswer(i,correct){

if(i==correct)
document.getElementById("result").innerHTML="Correct! 🎉"

else
document.getElementById("result").innerHTML="Wrong answer"

}

function generateNotes(){

let text=document.getElementById("textInput").value

let summary=text.split(".").slice(0,2).join(".")

document.getElementById("notesOutput").innerHTML=summary

}

function toggleDarkMode(){
  document.body.classList.toggle('dark-mode');
}

/* ========== Dark Mode Toggle ========== */
function toggleDarkMode(){
  document.body.classList.toggle('dark-mode');
}

/* ========== Notes AI Placeholder ========== */
function generateNotes(){
  const textInput = document.getElementById("textInput");
  const notesOutput = document.getElementById("notesOutput");

  if(textInput){
    let text = textInput.value;
    let summary = text.split(".").slice(0,2).join(".");
    notesOutput.innerHTML = summary || "No text provided";
  }

  const pdfInput = document.getElementById('pdfInput');
  const notesArea = document.getElementById('notesOutput');
  if(pdfInput && notesArea){
    const file = pdfInput.files[0];
    if(!file){ return; }
    notesArea.value = "Processing " + file.name + "...\n\nAI-generated notes will appear here!";
  }
}

/* ========== Progress Chart Upgrade ========== */
const ctx = document.getElementById('progressChart');
if(ctx){
  const gradient = ctx.getContext('2d').createLinearGradient(0,0,0,400);
  gradient.addColorStop(0, '#6a11cb');
  gradient.addColorStop(1, '#2575fc');

  new Chart(ctx, {
    type:'bar',
    data:{
      labels:['Algorithms','Networking','DSA','AI','Math'],
      datasets:[{
        label:'Progress %',
        data:[70,50,40,60,80],
        backgroundColor: gradient,
        borderRadius:10
      }]
    },
    options:{
      responsive:true,
      plugins:{ legend:{display:false}, tooltip:{mode:'index'} },
      scales:{ y:{beginAtZero:true,max:100} }
    }
  });
}