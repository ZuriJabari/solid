from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productreview',
            name='helpful_votes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='productreview',
            name='is_verified_purchase',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='productreview',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='productreview',
            name='moderated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moderated_reviews', to='accounts.user'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='moderation_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='productreview',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='productreview',
            name='title',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productreview',
            name='unhelpful_votes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name='ReviewVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vote', models.CharField(choices=[('helpful', 'Helpful'), ('unhelpful', 'Unhelpful')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='products.productreview')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
            ],
            options={
                'unique_together': {('review', 'user')},
                'indexes': [models.Index(fields=['review', 'vote'], name='products_re_review__0a4e7b_idx')],
            },
        ),
    ] 