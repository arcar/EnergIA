const pythonService=require("../services/pythonService");

async function getDashboard(req,res){
    try{
        const resultat=await pythonService.getDashboard();
        res.json(resultat);
    }catch(error){
        console.log("Erreur dashboard :",error);
        res.status(500).json({
            success:false,
            message:"Impossible de récupérer les données du dashboard"
        });
    }
}

module.exports={getDashboard};