df_summary.index.names = ['INDEX']


# delete index row
            df_detail.reset_index(inplace=True)
            df_detail.rename(columns={'rowid': 'Sıra No'}, inplace=True)


# resetting index
            df_detail['Sıra No'] = df_detail.index