import numpy as np
import bootstrapped.bootstrap as bs
import pandas as pd
import bootstrapped.compare_functions as bs_compare
import bootstrapped.stats_functions as bs_stats
import os

from numpy.linalg import cholesky
import matplotlib.pyplot as plt



def real_pv_test(sample_size):
    df = pd.read_csv("0928-ctr.sql", sep='\t')
    df_1005 = pd.read_csv("1005-ctr.sql", sep='\t')


    total_pv = float(np.mean(df["exp_pv"]))
    total_pv_1005= float(np.mean(df_1005["exp_pv"]))
    pv_diff = total_pv-total_pv_1005

    p_out, p_in, flag = 0, 0, 0
    zero_out, zero_in, zero_flag = 0, 0, 0
    ab_out, ab_in, ab_flag = 0, 0, 0

    bucket_num=50
    #total_click_pv = float(np.mean(df["cli_pv"]))
    p_out, p_in, flag = 0, 0, 0
    c_out, c_in, c_flag = 0, 0, 0
    split_num = sample_size / bucket_num
    for i in range(0, 1000):
        print("{0}th sample--------------------".format(i))
        buck_index = np.floor(np.arange(0, sample_size) / split_num)
        #filename1 = "data/0928A{0}_{1}".format(sample_size,i)
        filename1, filename2, filename3 = "data/0928A1{1}_{0}".format(i,sample_size), "data/0928A2{1}_{0}".format(
            i,sample_size), "data/1005B{1}_{0}".format(i,sample_size)

        if os.path.exists(filename1) and os.path.exists(filename2) and os.path.exists(filename3):
            sample1, sample2, sample3 = pd.read_csv(filename1, sep='\t'), pd.read_csv(filename2, sep='\t'), pd.read_csv(filename3, sep='\t')
        else:
            sample1, sample2, sample3 = df.sample(n=sample_size), df.sample(n=sample_size), df_1005.sample(n=sample_size)
            sample1["bucket_index"], sample2["bucket_index"], sample3["bucket_index"] = buck_index, buck_index, buck_index
            sample1.to_csv(filename1, sep='\t')
            sample2.to_csv(filename2, sep='\t')
            sample3.to_csv(filename3, sep='\t')

        sample_0928 = sample1.groupby(['bucket_index'])["cli_pv", "exp_pv"].mean().add_suffix('_sum').reset_index()
        sample_0928_1 = sample2.groupby(['bucket_index'])["cli_pv", "exp_pv"].mean().add_suffix('_sum').reset_index()
        sample_1005 = sample3.groupby(['bucket_index'])["cli_pv", "exp_pv"].mean().add_suffix('_sum').reset_index()

        #####bootstrap#######
        ####total
        r = bs.bootstrap(sample_0928.exp_pv_sum.values, bs_stats.mean)

        point, low, high = r.value, r.lower_bound, r.upper_bound
        if total_pv >= low and total_pv <= high:
            p_in = p_in + 1
            flag = 1
        else:
            p_out = p_out + 1
            flag = 0
        print(
            "total,flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(flag, point - total_pv,
                                                                                      total_pv,
                                                                                      low, high, high - low))

        ####aa
        r = bs.bootstrap_ab(sample_0928.exp_pv_sum.values,
                            sample_0928_1.exp_pv_sum.values,
                            stat_func=bs_stats.mean,
                            compare_func=bs_compare.difference)


        # r = bs.bootstrap_ab(sample_0928.cli_pv_sum.values / sample_0928.exp_pv_sum.values,
        #                     sample_0928_1.cli_pv_sum.values / sample_0928_1.exp_pv_sum.values,
        #                     stat_func=bs_stats.mean,
        #                     compare_func=bs_compare.difference)
        point, low, high = r.value, r.lower_bound, r.upper_bound
        zero = 0.0
        if zero>=low and zero<=high:
            zero_in = zero_in + 1
            zero_flag = 1
        else:
            zero_out = zero_out + 1
            zero_flag = 0
        print("flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(zero_flag, point-zero, 0.0, low, high, high-low))


        ####ab
        r = bs.bootstrap_ab(sample_0928.exp_pv_sum.values,
                            sample_1005.exp_pv_sum.values,
                            stat_func=bs_stats.mean,
                            compare_func=bs_compare.difference)
        point, low, high = r.value, r.lower_bound, r.upper_bound

        if pv_diff >= low and pv_diff <= high:
            ab_in = ab_in + 1
            ab_flag = 1
        else:
            ab_out = ab_out + 1
            ab_flag = 0
        print("flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(ab_flag, point - pv_diff, pv_diff,
                                                                                  low, high, high - low))




        if i % 50 == 0 or i / 50 == 0 or i  == 999:
            # print("sample_size:{2},total,notcover:{0},cover:{1}".format(p_out, p_in,sample_size))
            # print("sample_size:{2},total,notcover:{0},cover:{1}".format(c_out, c_in,sample_size))
            print("total,not cover:{0},cover:{1}".format(p_out, p_in))
            print("aatest,not cover:{0},cover:{1}".format(zero_out, zero_in))
            print("abtest,not cover:{0},cover:{1}".format(ab_out, ab_in))


    print("end")


def real_data_test():
    r_aa, r_ab = [], []
    df = pd.read_csv("0928-ctr.sql", sep='\t')
    df_1005 = pd.read_csv("1005-ctr.sql", sep='\t')

    total_ctr = float(np.sum(df["cli_pv"])) / np.sum(df["exp_pv"])
    total_ctr_1005 = float(np.sum(df_1005["cli_pv"]) )/ np.sum(df_1005["exp_pv"])
    ctr_diff = total_ctr - total_ctr_1005

    p_out, p_in, flag = 0, 0, 0
    zero_out, zero_in, zero_flag = 0, 0, 0
    ab_out, ab_in, ab_flag = 0, 0, 0

    sample_size = 1000000
    bucket_num = 100
    split_num = sample_size / bucket_num

    total_diff=0
    total_width=0
    for i in range(0, 1000):
        print("{0}th sample--------------------".format(i))
        up_num = np.linspace(1,bucket_num,bucket_num)
        down_num = np.linspace(bucket_num, 1, bucket_num)
        up_down_list=np.append(up_num, down_num)
        buck_index=np.tile(up_down_list,split_num/2)
        filename1, filename2, filename3 = "data/0928A1_{0}".format(i), "data/0928A2_{0}".format(i), "data/1005B_{0}".format(i)


        if os.path.exists(filename1) and os.path.exists(filename2) and os.path.exists(filename3):
            sample1, sample2, sample3 = pd.read_csv(filename1, sep='\t'), pd.read_csv(filename2, sep='\t'), pd.read_csv(filename3, sep='\t')
        else:
            sample1, sample2, sample3 = df.sample(n=sample_size), df.sample(n=sample_size), df_1005.sample(n=sample_size)
            sample1, sample2, sample3 = sample1.sort_values(by=["exp_pv"], ascending=False),sample2.sort_values(by=["exp_pv"], ascending=False),sample3.sort_values(by=["exp_pv"], ascending=False)
            sample1["bucket_index"], sample2["bucket_index"], sample3["bucket_index"] = buck_index, buck_index, buck_index
            sample1.to_csv(filename1, sep='\t')
            # sample2.to_csv(filename2, sep='\t')
            # sample3.to_csv(filename3, sep='\t')


        # sample_ctr = float(sample1["cli_pv"].sum()) / sample1["exp_pv"].sum()
        # p=sample_ctr
        # sample_theta=np.sqrt(p*(1-p))
        # avg_theta=sample_theta/np.sqrt(sample1["exp_pv"].sum())
        #
        # sampleNo = bucket_num
        # exp_pv_sum = np.ones(sampleNo) * sample1["exp_pv"].sum() / sampleNo
        # mu = float(sample1["cli_pv"].sum())/sample1["exp_pv"].sum()*(exp_pv_sum)
        # sigma = sample_theta/np.sqrt(exp_pv_sum)*exp_pv_sum
        # np.random.seed(0)
        # s = np.random.normal(mu, sigma, sampleNo)
        # plt.subplot(141)
        # plt.hist(s, 30, normed=True)
        # plt.show()
        #
        # cli_pv_sum=s
        # r = bs.bootstrap(cli_pv_sum, bs_stats.mean, denominator_values=exp_pv_sum)


        sample_0928 = sample1.groupby(['bucket_index'])["cli_pv", "exp_pv"].sum().add_suffix('_sum').reset_index()
        # sample_0928_1 = sample2.groupby(['bucket_index'])["cli_pv", "exp_pv"].sum().add_suffix('_sum').reset_index()
        # sample_1005 = sample3.groupby(['bucket_index'])["cli_pv", "exp_pv"].sum().add_suffix('_sum').reset_index()



        #####bootstrap#######
        ####total
        r = bs.bootstrap(sample_0928.cli_pv_sum.values, bs_stats.mean, denominator_values=sample_0928.exp_pv_sum.values)
        # r = bs.bootstrap(sample_0928.cli_pv_sum.values / sample_0928.exp_pv_sum.values, bs_stats.mean)

        point, low, high = r.value, r.lower_bound, r.upper_bound
        if total_ctr >= low and total_ctr <= high:
            p_in = p_in + 1
            flag = 1
        else:
            p_out = p_out + 1
            flag = 0
        print(
            "total,flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(flag, point - total_ctr, total_ctr,
                                                                                     low, high, high - low))
        #
        # ####A A test
        # r = bs.bootstrap_ab(sample_0928.cli_pv_sum.values,
        #                     sample_0928_1.cli_pv_sum.values,
        #                     test_denominator=sample_0928.exp_pv_sum.values,
        #                     ctrl_denominator=sample_0928_1.exp_pv_sum.values,
        #                     stat_func=bs_stats.mean,
        #                     compare_func=bs_compare.difference)
        #
        # # r = bs.bootstrap_ab(sample_0928.cli_pv_sum.values / sample_0928.exp_pv_sum.values,
        # #                     sample_0928_1.cli_pv_sum.values / sample_0928_1.exp_pv_sum.values,
        # #                     stat_func=bs_stats.mean,
        # #                     compare_func=bs_compare.difference)
        # r_aa.append(r)
        # point, low, high = r.value, r.lower_bound, r.upper_bound
        # zero = 0.0
        # if zero >= low and zero <= high:
        #     zero_in = zero_in + 1
        #     zero_flag = 1
        # else:
        #     zero_out = zero_out + 1
        #     zero_flag = 0
        # print(
        #     "aatest,flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(zero_flag, point - zero, 0.0, low,
        #                                                                              high, high - low))
        #
        # ####A B test
        # r = bs.bootstrap_ab(sample_0928.cli_pv_sum.values,
        #                     sample_1005.cli_pv_sum.values,
        #                     test_denominator=sample_0928.exp_pv_sum.values,
        #                     ctrl_denominator=sample_1005.exp_pv_sum.values,
        #                     stat_func=bs_stats.mean,
        #                     compare_func=bs_compare.difference)
        #
        # # r = bs.bootstrap_ab(sample_0928.cli_pv_sum.values / sample_0928.exp_pv_sum.values,
        # #                     sample_1005.cli_pv_sum.values / sample_1005.exp_pv_sum.values,
        # #                     stat_func=bs_stats.mean,
        # #                     compare_func=bs_compare.difference)
        # point, low, high = r.value, r.lower_bound, r.upper_bound
        # r_ab.append(r)
        # if ctr_diff >= low and ctr_diff <= high:
        #     ab_in = ab_in + 1
        #     ab_flag = 1
        # else:
        #     ab_out = ab_out + 1
        #     ab_flag = 0
        # print("abtest,flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(ab_flag, point - ctr_diff,
        #                                                                                ctr_diff, low, high, high - low))
        #


        if i % 50 == 0 or i == 999:
            print("total,notcover:{0},cover:{1}".format(p_out, p_in))
            # print("aatest,notcover:{0},cover:{1}".format(zero_out, zero_in))
            # print("abtest,notcover:{0},cover:{1}".format(ab_out, ab_in))
            count=0
            for i in sample_0928.exp_pv_sum.values:
                print i
                count+=1
                if count==20:
                    break

    print("end")
    # bs_power.plot_power(r_aa)
    # bs_power.power_stats(r_aa)
    # bs_power.power_stats(r_ab)


def real_data_test10w():
    df = pd.read_csv("1005-ctr.sql", sep='\t')

    total_ctr = float(np.sum(df["cli_pv"])) / np.sum(df["exp_pv"])


    p_out, p_in, flag = 0, 0, 0


    z_out, z_in, z_flag = 0, 0, 0


    sample_size = 100000
    bucket_num = 50
    split_num = sample_size / bucket_num
    num_iterations = 10000
    for i in range(0, 1000):
        print("{0}th test--------------------".format(i))
        buck_index = np.floor(np.arange(0, sample_size) / split_num)
        filename1= "data/0928A1_{0}".format(i)

        if os.path.exists(filename1):
            sample1 = pd.read_csv(filename1, sep='\t')
        else:
            sample1 = df.sample(n=sample_size)
            sample1["bucket_index"]= buck_index
            sample1.to_csv(filename1, sep='\t')


        sample_0928 = sample1.groupby(['bucket_index'])["cli_pv", "exp_pv"].sum().add_suffix('_sum').reset_index()


        #####bootstrap#######

        r = bs.bootstrap(sample_0928.cli_pv_sum.values, bs_stats.mean, denominator_values=sample_0928.exp_pv_sum.values)


        point, low, high = r.value, r.lower_bound, r.upper_bound
        if total_ctr>=low and total_ctr<=high:
            p_in = p_in + 1
            flag = 1
        else:
            p_out = p_out + 1
            flag = 0
        print("flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(flag, point-total_ctr, total_ctr, low, high, high-low))

        if i%50==0 or i ==999:
            print("100w,50bucket.not cover:{0},cover:{1}".format(p_out, p_in))
            count=0
            for i in sample_0928.exp_pv_sum.values:
                print i
                count+=1
                if count==20:
                    break

    print("end")

def real_data_test3w():
    df = pd.read_csv("1005-ctr.sql", sep='\t')

    total_ctr = float(np.sum(df["cli_pv"])) / np.sum(df["exp_pv"])


    p_out, p_in, flag = 0, 0, 0


    z_out, z_in, z_flag = 0, 0, 0


    sample_size = 30000
    bucket_num = 50
    split_num = sample_size / bucket_num
    num_iterations = 10000
    for i in range(0, 1000):
        print("{0}th test--------------------".format(i))
        buck_index = np.floor(np.arange(0, sample_size) / split_num)
        filename1= "data/0928A30w_{0}".format(i)

        if os.path.exists(filename1):
            sample1 = pd.read_csv(filename1, sep='\t')
        else:
            sample1 = df.sample(n=sample_size)
            sample1["bucket_index"]= buck_index
            sample1.to_csv(filename1, sep='\t')


        sample_0928 = sample1.groupby(['bucket_index'])["cli_pv", "exp_pv"].sum().add_suffix('_sum').reset_index()


        #####bootstrap#######

        r = bs.bootstrap(sample_0928.cli_pv_sum.values, bs_stats.mean, denominator_values=sample_0928.exp_pv_sum.values)


        point, low, high = r.value, r.lower_bound, r.upper_bound
        if total_ctr>=low and total_ctr<=high:
            p_in = p_in + 1
            flag = 1
        else:
            p_out = p_out + 1
            flag = 0
        print("flag:{0}, diff:{1}, real:{2}, low:{3}, high:{4}, width:{5}".format(flag, point-total_ctr, total_ctr, low, high, high-low))

        if i%50==0 or i ==999:
            print("30w,50bucket,not cover:{0},cover:{1}".format(p_out, p_in))
            count=0
            for i in sample_0928.exp_pv_sum.values:
                print i
                count+=1
                if count==20:
                    break

    print("end")

if __name__ == "__main__":
    sample_sizes = [100000,300000]
    for b in sample_sizes:
        real_pv_test(b)
    # real_data_test3w()
    # real_data_test10w()


