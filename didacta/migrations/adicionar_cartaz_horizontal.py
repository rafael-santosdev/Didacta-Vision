from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', 'remover_unique_titulo_e_trailer_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='film',
            name='cartaz',
            field=models.ImageField(
                help_text='Imagem vertical do cartaz do filme',
                null=True,
                upload_to='filmes/cartazes/',
                verbose_name='Cartaz Vertical',
            ),
        ),
        migrations.AddField(
            model_name='film',
            name='cartaz_horizontal',
            field=models.ImageField(
                help_text='Imagem horizontal usada como fundo nas páginas do filme',
                null=True,
                upload_to='filmes/cartazes/horizontais/',
                verbose_name='Cartaz Horizontal',
            ),
        ),
    ]
