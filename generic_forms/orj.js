<head>
    <link rel="stylesheet" href="https://bootswatch.com/4/superhero/bootstrap.css">
</head>

<img src="https://upload.wikimedia.org/wikipedia/en/6/66/Isdemir_logo.PNG" alt="Isdemir Logo">

<table class="table table-hover" id="mytable">
    <thead>
    <tr>
        <th scope="col">Yapı NO</th>
        <th scope="col">Yapı NO</th>
        <th scope="col">Yapı Adı</th>
        <th scope="col">Açıklama</th>
        <th scope="col">Taban alanı</th>
        <th scope="col">Yapı Mülkiyeti</th>
        <th scope="col">Yapı Sınıfı</th>
        <th scope="col">Yapı Ünitesi</th>
        <th scope="col">Mahalle / Köy</th>

    </tr>
    </thead>
    <tbody>
    <tr class="table-active" id="abc">
        <td>{eski_yapi_no}</td>
        <td>{eski_yapi_adi}</td>
        <td>{aciklama}</td>
        <td>{tabanalani}</td>
        <td>{yapimulkiyeti}</td>
        <td>{yapisinifi}</td>
        <td>{unite}</td>
        <td>{mahalle_koy}</td>
    </tr>
    </tbody>
</table>

<style>
    #mytable {
        background-color: brown;
        width: 100%;
        height: 100%;
        table-layout: fixed;

    }

    #abc {
        color: white;
    }
</style>


<!--https://isdemircbs.isdemir.com.tr/server/rest/services/Isdemir_CBS_Base_Layer/FeatureServer/9/51/attachments/9-->
